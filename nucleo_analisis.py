# ------------------------------------------------------------
# nucleo_analisis.py
#
# Puente entre la interfaz gráfica y los analizadores del grupo.
# NO modifica rust_lexer.py, rust_parser.py ni rust_semantic.py:
# solo los importa y ejecuta sobre el código que recibe como texto,
# devolviendo resultados estructurados (tokens, árbol, tabla de
# símbolos, errores) y el contenido de los logs con el mismo
# formato que genera main.py.
# ------------------------------------------------------------
import os
import re
import sys
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from datetime import datetime
from io import StringIO

# PLY escribe advertencias en stderr al construir el lexer/parser.
# Con pythonw (sin consola) sys.stderr es None y eso haría fallar la importación.
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")

with redirect_stdout(StringIO()):
    import rust_lexer
    import rust_parser
    import rust_semantic

from rust_lexer import lexer, lexical_errors, find_column

FASE_LEXICO = "LÉXICO"
FASE_SINTACTICO = "SINTÁCTICO"
FASE_SEMANTICO = "SEMÁNTICO"

_PATRON_ERROR = re.compile(
    r"^\[ERROR (?P<fase>[^\]]+)\]\s*"
    r"(?:Línea (?P<linea>\d+)(?:, Columna (?P<columna>\d+))?\s*:?\s*)?"
    r"(?P<mensaje>.*)$",
    re.DOTALL,
)


# ============================================================
# Estructuras de resultados
# ============================================================

@dataclass
class ErrorAnalisis:
    fase: str
    linea: int | None
    columna: int | None
    mensaje: str        # mensaje sin el prefijo "[ERROR X] Línea N, Columna M:"
    original: str       # texto tal como lo reporta el analizador


@dataclass
class TokenInfo:
    tipo: str
    lexema: str
    valor: object
    linea: int
    columna: int
    inicio: int         # posición absoluta en el código
    fin: int


@dataclass
class SimboloInfo:
    nombre: str
    categoria: str
    tipo: str
    mutable: str
    linea: int | None
    ambito: str


@dataclass
class ResultadoLexico:
    tokens: list = field(default_factory=list)
    errores: list = field(default_factory=list)
    errores_texto: list = field(default_factory=list)


@dataclass
class ResultadoSintactico:
    ast: object = None
    errores: list = field(default_factory=list)
    errores_texto: list = field(default_factory=list)
    errores_lexicos_previos: int = 0


@dataclass
class ResultadoSemantico:
    simbolos: list = field(default_factory=list)
    errores: list = field(default_factory=list)
    errores_texto: list = field(default_factory=list)
    ast_disponible: bool = True
    errores_sintacticos_previos: int = 0
    errores_lexicos_previos: int = 0


def convertir_error(texto, fase_por_defecto):
    """Convierte '[ERROR LÉXICO] Línea 9, Columna 26: ...' en un ErrorAnalisis."""
    m = _PATRON_ERROR.match(texto.strip())
    if not m:
        return ErrorAnalisis(fase_por_defecto, None, None, texto.strip(), texto)
    fase = m.group("fase").strip().upper()
    if fase not in (FASE_LEXICO, FASE_SINTACTICO, FASE_SEMANTICO):
        fase = fase_por_defecto
    linea = int(m.group("linea")) if m.group("linea") else None
    columna = int(m.group("columna")) if m.group("columna") else None
    return ErrorAnalisis(fase, linea, columna, m.group("mensaje").strip(), texto)


def _posicion_error(texto):
    m = re.search(r"Línea (\d+)(?:, Columna (\d+))?", texto)
    if m is None:
        return float("inf"), 0
    return int(m.group(1)), int(m.group(2) or 0)


# ============================================================
# Análisis léxico
# ============================================================

def analisis_lexico(codigo):
    lexical_errors.clear()
    lexer.lineno = 1
    resultado = ResultadoLexico()
    with redirect_stdout(StringIO()):
        lexer.input(codigo)
        while True:
            tok = lexer.token()
            if not tok:
                break
            fin = lexer.lexpos
            resultado.tokens.append(TokenInfo(
                tipo=tok.type,
                lexema=codigo[tok.lexpos:fin],
                valor=tok.value,
                linea=tok.lineno,
                columna=find_column(codigo, tok),
                inicio=tok.lexpos,
                fin=fin,
            ))
    resultado.errores_texto = list(lexical_errors)
    resultado.errores = [convertir_error(e, FASE_LEXICO) for e in lexical_errors]
    lexical_errors.clear()
    return resultado


# ============================================================
# Análisis sintáctico (misma lógica que run_parser de main.py)
# ============================================================

_PATRON_FALTA_CIERRE = re.compile(r"Línea (\d+), Columna (\d+): Falta '.' para cerrar")
_PATRON_TOKEN_INESPERADO = re.compile(r"Línea (\d+), Columna (\d+): Token inesperado")


def _quitar_errores_en_cascada(errores):
    """Un delimitador sin cerrar se reporta dos veces: 'Falta ')' para cerrar '('' y,
    como consecuencia, 'Token inesperado' más adelante en la misma línea.
    Se conserva el primero (indica la causa) y se omite el segundo."""
    aperturas = {}
    for e in errores:
        m = _PATRON_FALTA_CIERRE.search(e)
        if m:
            linea, columna = int(m.group(1)), int(m.group(2))
            aperturas[linea] = min(columna, aperturas.get(linea, columna))
    resultado = []
    for e in errores:
        m = _PATRON_TOKEN_INESPERADO.search(e)
        if m and int(m.group(1)) in aperturas and int(m.group(2)) > aperturas[int(m.group(1))]:
            continue
        resultado.append(e)
    return resultado


def analisis_sintactico(codigo):
    rust_parser.syntax_errors.clear()
    lexical_errors.clear()
    rust_parser.lexer.lineno = 1
    resultado = ResultadoSintactico()
    with redirect_stdout(StringIO()):
        try:
            resultado.ast = rust_parser.parser.parse(codigo, lexer=rust_parser.lexer, tracking=True)
        except Exception as exc:  # una regla del parser lanzó una excepción
            resultado.ast = None
            rust_parser.syntax_errors.append(
                f"[ERROR SINTÁCTICO] El analizador se detuvo por un error interno: {exc}")
        try:
            for error in rust_parser.find_unclosed_delimiter_errors(codigo):
                if error not in rust_parser.syntax_errors:
                    rust_parser.syntax_errors.append(error)
        except Exception:
            pass
    errores = _quitar_errores_en_cascada(sorted(rust_parser.syntax_errors, key=_posicion_error))
    resultado.errores_lexicos_previos = len(lexical_errors)
    resultado.errores_texto = errores
    resultado.errores = [convertir_error(e, FASE_SINTACTICO) for e in errores]
    rust_parser.syntax_errors.clear()
    lexical_errors.clear()
    return resultado


# ============================================================
# Análisis semántico + captura de la tabla de símbolos
# ============================================================

class _TablaConRegistro(rust_semantic.TablaSimbolos):
    """Igual que la tabla original, pero guarda una copia de cada declaración
    (con su nivel de ámbito) para poder mostrarla en la interfaz."""

    def __init__(self, analizador):
        super().__init__()
        self._analizador = analizador

    def declarar(self, simbolo):
        super().declarar(simbolo)
        self._analizador._registrar(simbolo, len(self.ambitos) - 1)


class _AnalizadorConRegistro(rust_semantic.AnalizadorSemantico):
    def __init__(self, fuente):
        super().__init__(fuente)
        self.tabla = _TablaConRegistro(self)
        self.registro = []
        self._funciones_activas = []
        self._lineas_sentencia = []

    # --- utilidades para conocer la línea de cada declaración ---
    def _linea_de_fn(self, nombre):
        m = re.search(r"\bfn\s+" + re.escape(nombre) + r"\b", self.fuente)
        return self.fuente.count("\n", 0, m.start()) + 1 if m else None

    def _primera_posicion(self, nodo):
        mejor = None
        pila = [nodo]
        while pila:
            actual = pila.pop()
            if isinstance(actual, list):
                pila.extend(actual)
            elif isinstance(actual, tuple) and actual:
                pos = rust_semantic.posicion_de(actual)
                if isinstance(pos, int) and not isinstance(pos, bool):
                    mejor = pos if mejor is None else min(mejor, pos)
                pila.extend(x for x in actual[1:] if isinstance(x, (tuple, list)))
        return mejor

    def visitar_sentencia(self, s):
        linea = None
        if isinstance(s, tuple) and s:
            if s[0] == "fn":
                linea = self._linea_de_fn(s[1])
            else:
                linea, _ = self.linea_columna(self._primera_posicion(s))
        self._lineas_sentencia.append(linea)
        try:
            super().visitar_sentencia(s)
        finally:
            self._lineas_sentencia.pop()

    def visitar_funcion(self, nombre, params, retorno, cuerpo):
        self._funciones_activas.append(nombre)
        self._lineas_sentencia.append(self._linea_de_fn(nombre))
        try:
            super().visitar_funcion(nombre, params, retorno, cuerpo)
        finally:
            self._lineas_sentencia.pop()
            self._funciones_activas.pop()

    def _registrar(self, simbolo, nivel):
        linea, _ = self.linea_columna(simbolo.pos)
        if linea is None:
            linea = next((l for l in reversed(self._lineas_sentencia) if l), None)
        self.registro.append((simbolo, nivel, linea,
                              self._funciones_activas[-1] if self._funciones_activas else None))

    # --- conversión a filas para la interfaz ---
    def texto_tipo(self, tipo):
        normal = self.normalizar_tipo(tipo)
        if normal is None:
            return "—"
        return self.nombre_tipo(self.materializar_tipo(normal))

    def firma(self, params, retorno):
        tipos = []
        for p in params:
            if p[0] == "param":
                tipos.append(self.texto_tipo(p[2]))
            elif p[0] == "receiver":
                tipos.append(p[1])
        texto = "(" + ", ".join(tipos) + ")"
        if retorno is not None:
            texto += " -> " + self.texto_tipo(retorno)
        return texto

    def filas_tabla(self, ast):
        filas = []
        sentencias = ast[1] if isinstance(ast, tuple) and ast and ast[0] == "program" else []

        # Funciones, structs e impl (recorriendo todo el árbol)
        pila = list(sentencias)
        vistos = set()
        while pila:
            s = pila.pop(0)
            if isinstance(s, list):
                pila[:0] = s
                continue
            if not isinstance(s, tuple) or not s:
                continue
            if s[0] == "fn":
                nombre, params, retorno, cuerpo = rust_semantic.normalizar_fn(s)
                if ("fn", nombre) not in vistos:
                    vistos.add(("fn", nombre))
                    filas.append(SimboloInfo(nombre, "función", self.firma(params, retorno), "—",
                                             self._linea_de_fn(nombre), "global"))
                pila[:0] = [cuerpo]
            elif s[0] == "struct":
                campos = ", ".join(f"{c[1]}: {self.texto_tipo(c[2])}" for c in s[2]
                                   if isinstance(c, tuple) and c and c[0] == "field")
                m = re.search(r"\bstruct\s+" + re.escape(s[1]) + r"\b", self.fuente)
                linea = self.fuente.count("\n", 0, m.start()) + 1 if m else None
                filas.append(SimboloInfo(s[1], "struct", "{ " + campos + " }" if campos else "{ }",
                                         "—", linea, "global"))
            elif s[0] == "impl":
                for metodo in s[2]:
                    _, nombre, params, retorno, cuerpo, _ = metodo
                    filas.append(SimboloInfo(nombre, "método", self.firma(params, retorno), "—",
                                             self._linea_de_fn(nombre), f"impl {s[1]}"))
            elif s[0] == "block":
                pila[:0] = [s[1]]
            elif s[0] in ("if", "while", "for"):
                pila[:0] = [x for x in s[1:] if isinstance(x, (tuple, list))]

        categorias = {
            "variable": "variable", "constante": "constante", "parametro": "parámetro",
            "iterador": "iterador (for)", "patron": "patrón (match)", "self": "self",
        }
        for simbolo, nivel, linea, funcion in self.registro:
            if nivel == 0:
                ambito = "global"
            elif funcion:
                # visitar_funcion abre un ámbito y el bloque del cuerpo otro más
                ambito = f"local: {funcion} (nivel {max(nivel - 1, 1)})"
            else:
                ambito = f"bloque (nivel {nivel})"
            if simbolo.categoria == "constante":
                mutable = "no"
            elif simbolo.categoria in ("iterador", "patron"):
                mutable = "no"
            else:
                mutable = "sí" if simbolo.mutable else "no"
            tipo = self.texto_tipo(simbolo.tipo)
            if simbolo.categoria == "self":
                tipo = getattr(simbolo, "receptor", "self")
            filas.append(SimboloInfo(simbolo.nombre, categorias.get(simbolo.categoria, simbolo.categoria),
                                     tipo, mutable, linea, ambito))

        filas.sort(key=lambda f: (f.linea if f.linea is not None else 10**9))
        return filas


def analisis_semantico(codigo, sintactico=None):
    """Ejecuta el análisis semántico (necesita el árbol del sintáctico).
    Igual que main.py, se ejecuta aunque existan errores previos, y se avisa."""
    if sintactico is None:
        sintactico = analisis_sintactico(codigo)
    resultado = ResultadoSemantico(
        errores_sintacticos_previos=len(sintactico.errores),
        errores_lexicos_previos=sintactico.errores_lexicos_previos,
    )
    if sintactico.ast is None:
        resultado.ast_disponible = False
        return resultado

    analizador = _AnalizadorConRegistro(codigo)
    with redirect_stdout(StringIO()):
        try:
            errores = analizador.analizar(sintactico.ast)
        except Exception as exc:
            errores = analizador.lista_errores() + [
                f"[ERROR SEMÁNTICO] El analizador se detuvo por un error interno: {exc}"]
        try:
            resultado.simbolos = analizador.filas_tabla(sintactico.ast)
        except Exception:
            resultado.simbolos = []
    resultado.errores_texto = list(errores)
    resultado.errores = [convertir_error(e, FASE_SEMANTICO) for e in errores]
    return resultado


# ============================================================
# Logs (mismo formato y nombres que main.py)
# ============================================================

TIPOS_LOG = ("lexico", "sintactico", "semantico")


def nombre_log(tipo, usuario, ahora=None):
    ahora = ahora or datetime.now()
    if tipo == "lexico":
        return f"lexico-{usuario}-{ahora.strftime('%d-%m-%Y-%Hh%M')}.txt"
    if tipo == "sintactico":
        return f"sintactico-{usuario}-{ahora.strftime('%Y%m%d-%Hh%M')}.txt"
    return f"semantico-{usuario}-{ahora.strftime('%d%m%Y-%Hh%M')}.txt"


def contenido_log(tipo, codigo, archivo, usuario, ahora=None, resultado=None):
    """Genera el texto del log. `resultado` permite reutilizar un análisis ya hecho."""
    ahora = ahora or datetime.now()
    fecha = ahora.strftime('%d/%m/%Y %H:%M:%S')
    if tipo == "lexico":
        res = resultado or analisis_lexico(codigo)
        lineas = [
            f"--- Log de análisis léxico ({usuario}) ---",
            f"Archivo analizado: {archivo}",
            f"Fecha y Hora: {fecha}\n",
            "--- Tokens reconocidos ---",
        ]
        for t in res.tokens:
            lineas.append(f"Token(tipo='{t.tipo}', valor='{t.valor}', línea={t.linea}, columna={t.columna})")
        lineas.append("\n--- Errores léxicos detectados ---")
        lineas += res.errores_texto or ["Ningún error léxico detectado."]
        return "\n".join(lineas)

    if tipo == "sintactico":
        res = resultado or analisis_sintactico(codigo)
        lineas = [
            f"--- Log de análisis sintáctico ({usuario}) ---",
            f"Archivo analizado: {archivo}",
            f"Fecha y Hora: {fecha}\n",
            "--- Errores sintácticos detectados ---",
        ]
        lineas += res.errores_texto or ["Ningún error sintáctico detectado."]
        return "\n".join(lineas)

    res = resultado or analisis_semantico(codigo)
    lineas = [
        f"--- Log de análisis semántico ({usuario}) ---",
        f"Archivo analizado: {archivo}",
        f"Fecha y Hora: {fecha}\n",
    ]
    if not res.ast_disponible:
        lineas.append("[AVISO] No se pudo construir el árbol sintáctico; "
                      "corrija los errores sintácticos para ejecutar el análisis semántico.\n")
    elif res.errores_sintacticos_previos:
        lineas.append(f"[AVISO] El archivo tiene {res.errores_sintacticos_previos} error(es) sintáctico(s); "
                      "el análisis semántico puede estar incompleto.\n")
    lineas.append("--- Errores semánticos detectados ---")
    lineas += res.errores_texto or ["Ningún error semántico detectado."]
    return "\n".join(lineas)


# ============================================================
# Árbol sintáctico -> nodos legibles para la interfaz
# ============================================================

# Nombre de cada campo de los nodos que construye rust_parser.py.
# '@' marca una posición (lexpos) que no se muestra.
CAMPOS_NODO = {
    "let": ("mutable", "nombre", "tipo", "valor", "@"),
    "const": ("nombre", "tipo", "valor", "@"),
    "assign": ("destino", "operador", "valor"),
    "binop": ("operador", "izquierda", "derecha"),
    "neg": ("operando",),
    "not": ("operando",),
    "lit": ("valor", "@"),
    "var": ("nombre", "@"),
    "array": ("elementos",),
    "tuple": ("elementos",),
    "vec": ("elementos",),
    "vec_repeat": ("valor", "cantidad"),
    "index": ("arreglo", "índice"),
    "field_access": ("objeto", "campo"),
    "while": ("condición", "cuerpo"),
    "if": ("condición", "entonces", "sino"),
    "match": ("expresión", "brazos"),
    "match_arm": ("patrón", "resultado"),
    "pattern": ("valor",),
    "pattern_literal": ("valor",),
    "param": ("nombre", "tipo", "mutable"),
    "call": ("función", "argumentos", "@"),
    "expr_stmt": ("expresión",),
    "struct": ("nombre", "campos", "público"),
    "field": ("nombre", "tipo", "público"),
    "assoc_call": ("tipo", "función", "argumentos"),
    "method_call": ("objeto", "método", "argumentos"),
    "path_call": ("ruta", "argumentos"),
    "for": ("variable", "iterador", "cuerpo"),
    "range": ("operador", "inicio", "fin"),
    "return": ("valor", "@"),
    "print_macro": ("macro", "argumentos"),
    "use": ("ruta",),
    "borrow_mut": ("valor",),
    "impl": ("tipo", "métodos"),
    "method": ("nombre", "parámetros", "retorno", "cuerpo", "público"),
    "receiver": ("tipo",),
}

NOMBRES_NODO = {
    "program": "programa", "block": "bloque", "let": "declaración let",
    "const": "constante", "assign": "asignación", "binop": "operación",
    "neg": "negativo", "not": "negación", "array": "arreglo", "tuple": "tupla",
    "vec": "vec!", "vec_repeat": "vec! repetición", "index": "acceso índice",
    "field_access": "acceso campo", "while": "while", "if": "if", "match": "match",
    "match_arm": "brazo", "fn": "función", "param": "parámetro", "call": "llamada",
    "expr_stmt": "sentencia expresión", "struct": "struct", "field": "campo",
    "assoc_call": "llamada asociada", "method_call": "llamada método",
    "path_call": "llamada ruta", "for": "for", "range": "rango", "return": "return",
    "print_macro": "macro impresión", "use": "use", "borrow_mut": "&mut",
    "impl": "impl", "method": "método", "receiver": "receptor",
    "invalid_statement": "sentencia inválida", "wildcard": "comodín _",
}

_TIPOS = ("type", "named_type", "array_type", "tuple_type", "vec_type")


def texto_tipo_ast(t):
    if t is None:
        return "—"
    if not isinstance(t, tuple) or not t:
        return str(t)
    if t[0] in ("type", "named_type"):
        return str(t[1])
    if t[0] == "vec_type":
        return f"Vec<{texto_tipo_ast(t[1])}>"
    if t[0] == "tuple_type":
        return "(" + ", ".join(texto_tipo_ast(x) for x in t[1]) + ")"
    if t[0] == "array_type":
        return f"[{texto_tipo_ast(t[1])}; {resumen_hoja(t[2]) or '…'}]"
    return str(t)


def resumen_hoja(n):
    """Texto corto para nodos simples; None si el nodo necesita desplegarse."""
    if isinstance(n, bool):
        return "sí" if n else "no"
    if n is None:
        return "—"
    if isinstance(n, (int, float, str)):
        return str(n)
    if isinstance(n, tuple) and n:
        if n[0] == "lit":
            return f"literal {n[1]}"
        if n[0] == "var":
            return f"identificador {n[1]}"
        if n[0] in _TIPOS:
            return texto_tipo_ast(n)
        if n[0] == "wildcard":
            return "_"
        if n[0] in ("pattern", "pattern_literal"):
            return f"patrón {n[1]}"
        if n[0] == "receiver":
            return f"receptor {n[1]}"
    return None


def campos_de(nodo):
    """Pares (campo, valor) visibles de un nodo del árbol."""
    tag = nodo[0]
    if tag == "fn":
        nombre, params, retorno, cuerpo = rust_semantic.normalizar_fn(nodo)
        return [("nombre", nombre), ("parámetros", params), ("retorno", retorno), ("cuerpo", cuerpo)]
    if tag == "block":
        return [(None, s) for s in nodo[1]]
    if tag == "program":
        return [(None, s) for s in nodo[1]]
    nombres = CAMPOS_NODO.get(tag)
    valores = nodo[1:]
    if nombres is None:
        return [(None, v) for v in valores]
    return [(n, v) for n, v in zip(nombres, valores) if n != "@"]


def linea_de_nodo(nodo, codigo):
    if isinstance(nodo, tuple) and nodo and nodo[0] in ("fn", "struct", "impl", "method"):
        palabra = "fn" if nodo[0] == "method" else nodo[0]
        m = re.search(rf"\b{palabra}\s+{re.escape(str(nodo[1]))}\b", codigo)
        if m:
            return codigo.count("\n", 0, m.start()) + 1
    pos = None
    pila = [nodo]
    while pila:
        actual = pila.pop()
        if isinstance(actual, list):
            pila.extend(actual)
        elif isinstance(actual, tuple) and actual:
            p = rust_semantic.posicion_de(actual)
            if isinstance(p, int) and not isinstance(p, bool):
                pos = p if pos is None else min(pos, p)
            pila.extend(x for x in actual[1:] if isinstance(x, (tuple, list)))
    if pos is None:
        return None
    return codigo.count("\n", 0, pos) + 1
