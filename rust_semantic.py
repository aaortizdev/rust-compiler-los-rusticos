# ------------------------------------------------------------
# rust_semantic.py
#
# Analizador semántico para un subconjunto de Rust.
# Recorre el árbol que genera rust_parser.py y reporta los
# errores semánticos encontrados.
# ------------------------------------------------------------
import re

# ==================
# Reglas compartidas
# ==================

# ==============================================================
# INICIO APORTE: @aaortizdev (Ariel Ortiz)
# Base del analizador: tabla de símbolos con ámbitos y recorrido
# del árbol.
# ==============================================================

class Simbolo:
    """Una entrada de la tabla de símbolos"""
    def __init__(self, nombre, categoria, tipo=None, mutable=False, pos=None):     
        self.nombre = nombre
        self.categoria = categoria
        self.tipo = tipo
        self.mutable = mutable
        self.pos = pos

class TablaSimbolos:
    """Tabla de símbolos con ámbitos anidados. Cada bloque { } abre un ámbito nuevo."""
    def __init__(self):
        self.ambitos = [{"simbolos": {}, "frontera_funcion": False}]

    def abrir_ambito(self, frontera_funcion=False):
        self.ambitos.append({"simbolos": {}, "frontera_funcion": frontera_funcion})

    def cerrar_ambito(self):
        self.ambitos.pop()

    def declarar(self, simbolo):
        self.ambitos[-1]["simbolos"][simbolo.nombre] = simbolo

    def buscar(self, nombre):
        """Devuelve (simbolo, accesible).

        - (None, False): el nombre no existe en ningún ámbito.
        - (simbolo, False): existe, pero es una variable local de otra
          función y no se puede usar desde la función actual.
        - (simbolo, True): existe y se puede usar.
        """
        cruzo_funcion = False
        encontrado_inaccesible = None
        for ambito in reversed(self.ambitos):
            simbolo = ambito["simbolos"].get(nombre)
            if simbolo is not None:
                if not cruzo_funcion or simbolo.categoria == "constante":
                    return simbolo, True
                if encontrado_inaccesible is None:
                    encontrado_inaccesible = simbolo
            if ambito["frontera_funcion"]:
                cruzo_funcion = True
        return encontrado_inaccesible, False

def normalizar_fn(nodo):
    """El parser genera las funciones con formas distintas:
         ('fn', nombre, cuerpo)
         ('fn', nombre, params, cuerpo)
         ('fn', nombre, params, tipo_retorno, cuerpo)
    Esta función siempre devuelve (nombre, params, tipo_retorno, cuerpo)."""
    if len(nodo) == 3:
        return nodo[1], [], None, nodo[2]
    if len(nodo) == 4:
        return nodo[1], nodo[2], None, nodo[3]
    return nodo[1], nodo[2], nodo[3], nodo[4]


def posicion_de(nodo):
    """lexpos guardado en el nodo, o None si ese nodo no lo trae."""
    if not isinstance(nodo, tuple) or not nodo:
        return None
    indices = {"var": 2, "lit": 2, "let": 5, "const": 4}
    indice = indices.get(nodo[0])
    if indice is not None and len(nodo) > indice:
        return nodo[indice]
    return None

class AnalizadorSemantico:

    def __init__(self, fuente):
        self.fuente = fuente
        self.errores = []   #lista de (linea, columna, mensaje)
        self.tabla = TablaSimbolos()
        self.funciones = set() # nombres de funciones definidas

    # -------------------- utilidades ----------------------------
    
    def linea_columna(self, pos):
        if pos is None:
            return None, None
        linea = self.fuente.count("\n", 0, pos) + 1
        inicio_linea = self.fuente.rfind("\n", 0, pos) + 1
        return linea, pos - inicio_linea + 1

    def error(self, mensaje, pos=None):
        linea, columna = self.linea_columna(pos)
        if linea is None:
            texto = f"[ERROR SEMÁNTICO] {mensaje}"
        else:
            texto = f"[ERROR SEMÁNTICO] Línea {linea}, Columna {columna}: {mensaje}"
        self.errores.append((linea or float("inf"), columna or 0, texto))

    def lista_errores(self):
        return [texto for _, _, texto in sorted(self.errores, key=lambda e: (e[0], e[1]))]

    # -------------------- registro previo -----------------------
    # En Rust las funciones y contantes se pueden usar antes de la
    # línea donde se definen, así que se registran antes de 
    # recorrer las sentencias de cada bloque. 

    def registrar_elementos(self, sentencias):
        for s in sentencias:
            if not isinstance(s, tuple) or not s:
                continue
            if s[0] == "fn":
                self.funciones.add(s[1])
            elif s[0] == "const":
                self.tabla.declarar(Simbolo(s[1], "constante", s[2], False, posicion_de(s)))

    # ----------------------------- recorrido --------------------

    def analizar(self, ast):
        if ast is None:
            return self.lista_errores()
        sentencias = ast[1] if ast[0] == "program" else ast
        self.registrar_elementos(sentencias)
        for s in sentencias:
            self.visitar_sentencia(s)
        return self.lista_errores()

    def visitar_bloque(self, bloque, simbolos_previos=()):
        """Abre un ámbito, declara simbolos_previos (parámetros, variable del
        for, etc.), recorre las sentencias y cierra el ámbito."""
        sentencias = bloque[1] if isinstance(bloque, tuple) and bloque[0] == "block" else []
        self.tabla.abrir_ambito()
        for simbolo in simbolos_previos:
            self.tabla.declarar(simbolo)
        self.registrar_elementos(sentencias)
        for s in sentencias:
            self.visitar_sentencia(s)
        self.tabla.cerrar_ambito()

    def visitar_sentencia(self, s):
        if not isinstance(s, tuple) or not s:
            return
        tag = s[0]

        if tag == "let":
            mutable, nombre, tipo, valor = s[1], s[2], s[3], s[4]
            self.visitar_expr(valor)
            self.tabla.declarar(Simbolo(nombre, "variable", tipo, mutable, posicion_de(s)))

        elif tag == "const":
            self.visitar_expr(s[3])

        elif tag == "assign":
            self.visitar_expr(s[1])
            self.visitar_expr(s[3])
            self.regla_mutabilidad_asignacion(s)

        elif tag == "while":
            self.visitar_expr(s[1])
            self.visitar_bloque(s[2])

        elif tag == "if":
            self.visitar_expr(s[1])
            self.visitar_bloque(s[2])
            otro = s[3]
            if isinstance(otro, tuple) and otro[0] == "if":
                self.visitar_sentencia(otro)
            elif otro is not None:
                self.visitar_bloque(otro)

        elif tag == "for":
            variable, iterador, cuerpo = s[1], s[2], s[3]
            if isinstance(iterador, tuple) and iterador[0] == "range":
                self.visitar_expr(iterador[2])
                self.visitar_expr(iterador[3])
            else:
                self.visitar_expr(iterador)
            self.visitar_bloque(cuerpo, [Simbolo(variable, "iterador")])

        elif tag == "match":
            self.visitar_match(s)

        elif tag == "fn":
            nombre, params, retorno, cuerpo = normalizar_fn(s)
            self.visitar_funcion(nombre, params, retorno, cuerpo)

        elif tag == "impl":
            for metodo in s[2]:
                _, nombre, params, retorno, cuerpo, _ = metodo
                self.visitar_funcion(nombre, params, retorno, cuerpo)

        elif tag == "return":
            if s[1] is not None:
                self.visitar_expr(s[1])

        elif tag == "print_macro":
            for arg in s[2]:
                self.visitar_expr(arg)
            self.regla_identificadores_en_formato(s)

        elif tag == "expr_stmt":
            self.visitar_expr(s[1])

    def visitar_funcion(self, nombre, params, retorno, cuerpo):
        self.tabla.abrir_ambito(frontera_funcion=True)
        simbolos = []
        for p in params:
            if p[0] == "param":
                simbolos.append(Simbolo(p[1], "parametro", p[2], p[3]))
            elif p[0] == "receiver":
                mutable = p[1] in ("&mut self", "mut self")
                simbolos.append(Simbolo("self", "self", None, mutable))
                simbolos[-1].receptor = p[1]
        self.visitar_bloque(cuerpo, simbolos)
        self.tabla.cerrar_ambito()

    def visitar_match(self, nodo):
        self.visitar_expr(nodo[1])
        for brazo in nodo[2]:
            _, patron, cuerpo = brazo
            ligados = []
            if patron[0] == "pattern" and isinstance(patron[1], str):
                valor = patron[1]
                es_literal = valor in ("true", "false") or valor[:1] in ('"', "'")
                simbolo, accesible = self.tabla.buscar(valor)
                es_constante = simbolo is not None and accesible and simbolo.categoria == "constante"
                if not es_literal and not es_constante:
                    # Un identificador en un patrón crea una variable nueva.
                    ligados.append(Simbolo(valor, "patron"))
            if isinstance(cuerpo, tuple) and cuerpo[0] == "block":
                self.visitar_bloque(cuerpo, ligados)
            else:
                self.tabla.abrir_ambito()
                for simbolo in ligados:
                    self.tabla.declarar(simbolo)
                self.visitar_expr(cuerpo)
                self.tabla.cerrar_ambito()

    def visitar_expr(self, e):
        if not isinstance(e, tuple) or not e:
            return
        tag = e[0]

        if tag == "var":
            self.regla_identificador_declarado(e[1], posicion_de(e))

        elif tag == "binop":
            self.visitar_expr(e[2])
            self.visitar_expr(e[3])

        elif tag in ("neg", "not"):
            self.visitar_expr(e[1])

        elif tag in ("array", "tuple", "vec"):
            for elemento in e[1]:
                self.visitar_expr(elemento)

        elif tag == "vec_repeat":
            self.visitar_expr(e[1])
            self.visitar_expr(e[2])

        elif tag == "index":
            self.visitar_expr(e[1])
            self.visitar_expr(e[2])

        elif tag == "field_access":
            self.visitar_expr(e[1])

        elif tag == "call":
            for arg in e[2]:
                self.visitar_expr(arg)

        elif tag == "method_call":
            self.visitar_expr(e[1])
            for arg in e[3]:
                self.visitar_expr(arg)
            self.regla_mutabilidad_metodo(e)

        elif tag in ("assoc_call", "path_call"):
            for arg in e[-1]:
                self.visitar_expr(arg)

        elif tag == "borrow_mut":
            self.visitar_expr(e[1])
            self.regla_mutabilidad_prestamo(e)

        elif tag == "match":
            self.visitar_match(e)

    # --------------------------------------------------------------
    # Reglas semánticas de @aaortizdev
    # --------------------------------------------------------------

    # --------------------------------------------------------------
    # REGLA SEMÁNTICA 1: Identificadores declarados antes de su uso
    # --------------------------------------------------------------

    def regla_identificador_declarado(self, nombre, pos):
        simbolo, accesible = self.tabla.buscar(nombre)
        if simbolo is not None and accesible:
            return
        if nombre in self.funciones:
            return 
        if nombre == "self":
            self.error("'self' solo se puede usar dentro de un método de un bloque 'impl' "
                       "que lo reciba como parámetro.", pos)
        elif simbolo is not None:
            self.error(f"La variable '{nombre}' pertenece a otra función; una 'fn' no puede "
                       "usar variables locales declaradas fuera de ella.", pos)
        else:
            self.error(f"El identificador '{nombre}' no ha sido declarado en este ámbito.", pos)

    def regla_identificadores_en_formato(self, nodo):
        argumentos = nodo[2]
        if not argumentos:
            return
        formato = argumentos[0]
        if not (formato[0] == "lit" and isinstance(formato[1], str) and formato[1].startswith('"')):
            return
        texto = formato[1]
        inicio = posicion_de(formato)
        # '{{' y '}}' son llaves escritas literalmente; se tapan sin mover posiciones.
        texto_sin_escapes = texto.replace("{{", "  ").replace("}}", "  ")
        for m in re.finditer(r"\{([A-Za-z_][A-Za-z0-9_]*)(?::[^}]*)?\}", texto_sin_escapes):
            pos = inicio + m.start(1) if inicio is not None else None
            self.regla_identificador_declarado(m.group(1), pos)

    # ------------------------------------------------------------
    # REGLA SEMÁNTICA 2: Mutabilidad (let mut) y constantes.
    # ------------------------------------------------------------

    METODOS_QUE_MODIFICAN = {
        "push", "pop", "insert", "remove", "clear", "truncate", "sort",
        "sort_unstable", "reverse", "extend", "append", "push_str",
        "retain", "dedup", "drain", "swap", "resize", "split_off",
    }

    def variable_base(self, expr):
        """Variable que realmente se modifica: v en v[0], p en p.x, etc."""
        while isinstance(expr, tuple) and expr and expr[0] in ("index", "field_access"):
            expr = expr[1]
        if isinstance(expr, tuple) and expr and expr[0] == "var":
            return expr
        return None

    def simbolo_modificable(self, expr):
        base = self.variable_base(expr)
        if base is None:
            return None
        simbolo, accesible = self.tabla.buscar(base[1])
        if simbolo is None or not accesible:
            return None
        return base, simbolo

    def descripcion_inmutable(self, simbolo):
        nombre = simbolo.nombre
        if simbolo.categoria == "variable":
            linea, _ = self.linea_columna(simbolo.pos)
            donde = f" (declarada en la línea {linea})" if linea else ""
            return (f"la variable '{nombre}' es inmutable{donde}; declárala como "
                    f"'let mut {nombre}'")
        if simbolo.categoria == "parametro":
            return f"el parámetro '{nombre}' es inmutable; decláralo como 'mut {nombre}'"
        if simbolo.categoria == "iterador":
            return f"'{nombre}' es la variable del ciclo 'for' y no se puede modificar"
        if simbolo.categoria == "patron":
            return f"'{nombre}' es una variable de un patrón de 'match' y es inmutable"
        if simbolo.categoria == "self":
            receptor = getattr(simbolo, "receptor", "self")
            return (f"el método recibe '{receptor}'; para modificar 'self' debe "
                    "recibir '&mut self'")
        return f"'{nombre}' es inmutable"

    def regla_mutabilidad_asignacion(self, nodo):
        _, objetivo, operador, _ = nodo
        encontrado = self.simbolo_modificable(objetivo)
        if encontrado is None:
            return
        base, simbolo = encontrado
        pos = posicion_de(base)
        if simbolo.categoria == "constante":
            self.error(f"No se puede asignar ('{operador}') a la constante '{simbolo.nombre}': "
                       "las constantes no se pueden reasignar.", pos)
        elif not simbolo.mutable:
            self.error(f"No se puede asignar ('{operador}'): "
                       f"{self.descripcion_inmutable(simbolo)}.", pos)

    def regla_mutabilidad_prestamo(self, nodo):
        encontrado = self.simbolo_modificable(nodo[1])
        if encontrado is None:
            return
        base, simbolo = encontrado
        # '&mut CONSTANTE' crea una copia temporal, Rust lo permite.
        if simbolo.categoria != "constante" and not simbolo.mutable:
            self.error(f"No se puede tomar '&mut {simbolo.nombre}': "
                       f"{self.descripcion_inmutable(simbolo)}.", posicion_de(base))
    
    def regla_mutabilidad_metodo(self, nodo):
        """v.push(1) necesita que v sea mutable."""
        _, objeto, metodo, _ = nodo
        if metodo not in self.METODOS_QUE_MODIFICAN:
            return
        encontrado = self.simbolo_modificable(objeto)
        if encontrado is None:
            return
        base, simbolo = encontrado
        if simbolo.categoria != "constante" and not simbolo.mutable:
            self.error(f"No se puede llamar a '.{metodo}()', que modifica el valor: "
                       f"{self.descripcion_inmutable(simbolo)}.", posicion_de(base))

    # ============================================================
    # FIN APORTE: @aaortizdev (Ariel Ortiz)
    # ============================================================


    # ============================================================
    # INICIO APORTE: @jonaguilera13 (Carlos Aguilera)
    # ============================================================



    # ============================================================
    # FIN APORTE: @jonaguilera13 (Carlos Aguilera)
    # ============================================================


    # ============================================================
    # INICIO APORTE: @ChrisPal2307 (Christian Palma)
    # ============================================================



    # ============================================================
    # FIN APORTE: @ChrisPal2307 (Christian Palma)
    # ============================================================

def analizar(ast, fuente):
    """Punto de entrada: devuelve la lista de errores semánticos"""
    return AnalizadorSemantico(fuente).analizar(ast)