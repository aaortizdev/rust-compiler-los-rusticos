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
            self.regla_tipo_declaracion(nombre, tipo, valor, posicion_de(s))
            tipo_variable = tipo if tipo is not None else self.tipo_inferido_declaracion(valor)
            self.tabla.declarar(Simbolo(nombre, "variable", tipo_variable, mutable, posicion_de(s)))

        elif tag == "const":
            self.visitar_expr(s[3])
            self.regla_tipo_declaracion(s[1], s[2], s[3], posicion_de(s))

        elif tag == "assign":
            self.visitar_expr(s[1])
            self.visitar_expr(s[3])
            self.regla_mutabilidad_asignacion(s)
            self.regla_tipo_asignacion(s)

        elif tag == "while":
            self.visitar_expr(s[1])
            self.regla_condicion_booleana(s[1], "while")
            self.visitar_bloque(s[2])

        elif tag == "if":
            self.visitar_expr(s[1])
            self.regla_condicion_booleana(s[1], "if")
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
            self.regla_tipos_operacion(e)

        elif tag in ("neg", "not"):
            self.visitar_expr(e[1])
            if tag == "not":
                self.regla_negacion_booleana(e)

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
            self.regla_acceso_tupla(e)

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
    # Compatibilidad de tipos en declaraciones, asignaciones y operaciones binarias. Regla 2: condiciones y operadores lógicos obligatoriamente booleanos.
    # ============================================================

    ENTEROS = frozenset({
        "i8", "i16", "i32", "i64", "i128", "isize",
        "u8", "u16", "u32", "u64", "u128", "usize",
    })
    FLOTANTES = frozenset({"f32", "f64"})
    ARITMETICOS = frozenset({"+", "-", "*", "/", "%"})
    COMPARACIONES = frozenset({"==", "!=", "<", "<=", ">", ">="})

    #Convierte los nodos de tipo del parser a una forma comparable.
    def normalizar_tipo(self, tipo):
        if tipo is None or isinstance(tipo, str):
            return tipo
        if not isinstance(tipo, tuple):
            return None
        etiqueta = tipo[0]
        if etiqueta in ("type", "named_type"):
            return tipo[1]
        if etiqueta in ("tuple_type", "tuple"):
            return ("tuple", tuple(self.normalizar_tipo(t) for t in tipo[1]))
        if etiqueta in ("array_type", "array"):
            return ("array", self.normalizar_tipo(tipo[1]))
        if etiqueta in ("vec_type", "vec"):
            return ("vec", self.normalizar_tipo(tipo[1]))
        return None
    #Muestra tipos de forma comprensible en los errores.
    def nombre_tipo(self, tipo):
        if tipo == "entero_literal":
            return "entero"
        if tipo == "flotante_literal":
            return "decimal"
        if isinstance(tipo, tuple):
            if tipo[0] == "tuple":
                return "(" + ", ".join(self.nombre_tipo(t) for t in tipo[1]) + ")"
            if tipo[0] == "array":
                return "[" + self.nombre_tipo(tipo[1]) + "]"
            if tipo[0] == "vec":
                return "Vec<" + self.nombre_tipo(tipo[1]) + ">"
        return str(tipo)

    #Al inferir un let sin anotación, Rust usará i32 o f64 por defecto.
    def materializar_tipo(self, tipo):
        if tipo == "entero_literal":
            return "i32"
        if tipo == "flotante_literal":
            return "f64"
        if isinstance(tipo, tuple):
            if tipo[0] == "tuple":
                return ("tuple", tuple(self.materializar_tipo(t) for t in tipo[1]))
            return (tipo[0], self.materializar_tipo(tipo[1]))
        return tipo

    #No hace conversiones implícitas entre familias ni tipos distintos.
    def tipos_compatibles(self, esperado, recibido):
        if esperado is None or recibido is None:
            return True
        if esperado == recibido:
            return True
        if recibido == "entero_literal" and esperado in self.ENTEROS:
            return True
        if recibido == "flotante_literal" and esperado in self.FLOTANTES:
            return True
        if isinstance(esperado, tuple) and isinstance(recibido, tuple):
            if esperado[0] != recibido[0]:
                return False
            if esperado[0] == "tuple":
                return (len(esperado[1]) == len(recibido[1]) and
                        all(self.tipos_compatibles(a, b)
                            for a, b in zip(esperado[1], recibido[1])))
            if esperado[0] in ("array", "vec"):
                return self.tipos_compatibles(esperado[1], recibido[1])
        return False
    
    #Tipo resultante si ambos operandos son numéricos compatibles.
    def unificar_numericos(self, izquierdo, derecho):
        if izquierdo == derecho and izquierdo in (
                self.ENTEROS | self.FLOTANTES | {"entero_literal", "flotante_literal"}):
            return izquierdo
        if izquierdo == "entero_literal" and derecho in self.ENTEROS:
            return derecho
        if derecho == "entero_literal" and izquierdo in self.ENTEROS:
            return izquierdo
        if izquierdo == "flotante_literal" and derecho in self.FLOTANTES:
            return derecho
        if derecho == "flotante_literal" and izquierdo in self.FLOTANTES:
            return izquierdo
        return None

    #Igualdad para tipos iguales, orden solamente en números o caracteres.
    def tipos_comparables(self, izquierdo, derecho, operador):
        if operador in ("==", "!="):
            if izquierdo == derecho:
                return True
            return (self.unificar_numericos(izquierdo, derecho) is not None)
        return (self.unificar_numericos(izquierdo, derecho) is not None or
                (izquierdo == derecho == "char"))

    #Obtiene un tipo inferido sin emitir errores ni visitar dos veces el AST.
    def tipo_expresion(self, expr):
        if not isinstance(expr, tuple) or not expr:
            return None
        etiqueta = expr[0]

        if etiqueta == "lit":
            valor = expr[1]
            if isinstance(valor, bool) or valor in ("true", "false"):
                return "bool"
            if isinstance(valor, int):
                return "entero_literal"
            if isinstance(valor, float):
                return "flotante_literal"
            if isinstance(valor, str):
                if valor.startswith('"'):
                    return "&str"
                if valor.startswith("'"):
                    return "char"
            return None

        if etiqueta == "var":
            simbolo, accesible = self.tabla.buscar(expr[1])
            return self.normalizar_tipo(simbolo.tipo) if simbolo is not None and accesible else None

        if etiqueta == "binop":
            _, op, izquierdo, derecho = expr
            t_izq, t_der = self.tipo_expresion(izquierdo), self.tipo_expresion(derecho)
            if t_izq is None or t_der is None:
                return None
            if op in self.ARITMETICOS:
                return self.unificar_numericos(t_izq, t_der)
            if op in ("&&", "||"):
                return "bool" if t_izq == t_der == "bool" else None
            if op in self.COMPARACIONES:
                return "bool" if self.tipos_comparables(t_izq, t_der, op) else None
            return None

        if etiqueta == "not":
            return "bool" if self.tipo_expresion(expr[1]) == "bool" else None
        if etiqueta == "neg":
            t = self.tipo_expresion(expr[1])
            return t if t in (self.ENTEROS | self.FLOTANTES |
                              {"entero_literal", "flotante_literal"}) else None
        if etiqueta == "tuple":
            return ("tuple", tuple(self.tipo_expresion(e) for e in expr[1]))
        if etiqueta in ("array", "vec"):
            if not expr[1]:
                return None
            primero = self.tipo_expresion(expr[1][0])
            if primero is None or not all(
                    self.tipos_compatibles(primero, self.tipo_expresion(x))
                    for x in expr[1][1:]):
                return None
            return (etiqueta, primero)
        if etiqueta == "vec_repeat":
            tipo = self.tipo_expresion(expr[1])
            return ("vec", tipo) if tipo is not None else None
        if etiqueta == "index":
            tipo = self.tipo_expresion(expr[1])
            if isinstance(tipo, tuple) and tipo[0] in ("array", "vec"):
                return tipo[1]
        if etiqueta == "field_access":
            tipo = self.tipo_expresion(expr[1])
            indice = expr[2]
            if (isinstance(tipo, tuple) and tipo[0] == "tuple" and
                    isinstance(indice, int) and 0 <= indice < len(tipo[1])):
                return tipo[1][indice]
        return None

    def tipo_inferido_declaracion(self, expr):
        return self.materializar_tipo(self.tipo_expresion(expr))

    #Primer token conocido de la expresión, el AST no guarda operadores.
    def posicion_expresion(self, expr):
        pos = posicion_de(expr)
        if pos is not None:
            return pos
        if isinstance(expr, tuple) and expr:
            if expr[0] == "binop":
                izquierdo = self.posicion_expresion(expr[2])
                return izquierdo if izquierdo is not None else self.posicion_expresion(expr[3])
            if expr[0] in ("not", "neg", "index", "field_access", "borrow_mut"):
                return self.posicion_expresion(expr[1])
        return None
    
    # Regla Semántica 1- Compatibilidad de Tipos
    def regla_tipo_declaracion(self, nombre, tipo, valor, pos):
        esperado = self.normalizar_tipo(tipo)
        recibido = self.tipo_expresion(valor)
        if esperado is not None and recibido is not None and not self.tipos_compatibles(esperado, recibido):
            self.error(
                f"Tipo incompatible al declarar '{nombre}': se esperaba "
                f"'{self.nombre_tipo(esperado)}', pero se obtuvo "
                f"'{self.nombre_tipo(recibido)}'.",
                self.posicion_expresion(valor) if self.posicion_expresion(valor) is not None else pos,
            )

    def regla_tipo_asignacion(self, nodo):
        _, destino, operador, valor = nodo
        esperado = self.tipo_expresion(destino)
        recibido = self.tipo_expresion(valor)
        if esperado is None or recibido is None:
            return
        pos = self.posicion_expresion(destino)
        if operador == "=":
            valido = self.tipos_compatibles(esperado, recibido)
        elif operador in ("+=", "-=", "*=", "/=", "%="):
            # El resultado de la operación compuesta debe conservar el tipo.
            valido = self.unificar_numericos(esperado, recibido) == esperado
        elif operador in ("&=", "|=", "^="):
            valido = (esperado == recibido == "bool" or
                      (esperado in self.ENTEROS and self.tipos_compatibles(esperado, recibido)))
        elif operador in ("<<=", ">>="):
            valido = (esperado in self.ENTEROS and
                      (recibido in self.ENTEROS or recibido == "entero_literal"))
        else:
            return
        if not valido:
            self.error(
                f"Asignación '{operador}' incompatible: el destino es "
                f"'{self.nombre_tipo(esperado)}' y el valor es "
                f"'{self.nombre_tipo(recibido)}'.", pos)

    def regla_tipos_operacion(self, expr):
        _, op, izquierda, derecha = expr
        t_izq, t_der = self.tipo_expresion(izquierda), self.tipo_expresion(derecha)
        if op in ("&&", "||"):
            # La comprobación independiente permite detectar cada operando
            # incorrecto sin generar errores en cascada en los nodos padres.
            for lado, tipo, subexpr in (("izquierdo", t_izq, izquierda),
                                        ("derecho", t_der, derecha)):
                if tipo is not None and tipo != "bool":
                    self.error(
                        f"El operador lógico '{op}' requiere operandos 'bool': "
                        f"el operando {lado} es '{self.nombre_tipo(tipo)}'.",
                        self.posicion_expresion(subexpr))
        elif t_izq is not None and t_der is not None:
            if op in self.ARITMETICOS:
                valido = self.unificar_numericos(t_izq, t_der) is not None
            elif op in self.COMPARACIONES:
                valido = self.tipos_comparables(t_izq, t_der, op)
            else:
                return
            if not valido:
                self.error(
                    f"Operación '{op}' con tipos incompatibles: "
                    f"'{self.nombre_tipo(t_izq)}' y '{self.nombre_tipo(t_der)}'.",
                    self.posicion_expresion(expr))

    # Regla Semántica2- Condiciones y operadores lógicos bool
    def regla_condicion_booleana(self, expr, estructura):
        tipo = self.tipo_expresion(expr)
        if tipo is not None and tipo != "bool":
            self.error(f"La condición de '{estructura}' debe ser 'bool', "f"no '{self.nombre_tipo(tipo)}'.", self.posicion_expresion(expr))

    def regla_negacion_booleana(self, expr):
        tipo = self.tipo_expresion(expr[1])
        if tipo is not None and tipo != "bool":
            self.error(f"El operador lógico '!' requiere un operando 'bool', "f"no '{self.nombre_tipo(tipo)}'.", self.posicion_expresion(expr[1]))

    # Regla Semántica 3 (Como extra)- Acceso válido a elementos de una tupla   
    def regla_acceso_tupla(self, expr):
        _, tupla, indice = expr
        tipo = self.tipo_expresion(tupla)
        if not (isinstance(tipo, tuple) and tipo[0] == "tuple"):
            return
        if not isinstance(indice, int):
            return
        cantidad = len(tipo[1])
        if indice < 0 or indice >= cantidad:
            self.error(f"Índice {indice} fuera de rango, la tupla tiene {cantidad} "f"elementos (índices válidos: 0 a {cantidad - 1}).",self.posicion_expresion(tupla),)
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