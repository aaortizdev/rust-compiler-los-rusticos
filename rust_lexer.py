# ------------------------------------------------------------
# rust_lexer.py
#
# Analizador léxico para un subconjunto de Rust usando PLY
# ------------------------------------------------------------
import ply.lex as lex

lexical_errors = []

def find_column(input_text, token):
    line_start = input_text.rfind('\n', 0, token.lexpos) + 1
    return (token.lexpos - line_start) + 1

# ============================================================
# INICIO APORTE: @aaortizdev (Ariel Ortiz)
# ============================================================

# Palabras reservadas
reserved_aaortizdev = {
    # Declaraciones
    "as": "AS",
    "async": "ASYNC",
    "await": "AWAIT",
    "const": "CONST",
    "crate": "CRATE",
    "dyn": "DYN",
    "enum": "ENUM",
    "extern": "EXTERN",
    "fn": "FN",
    "impl": "IMPL",
    "let": "LET",
    "mod": "KW_MOD",
    "move": "MOVE",
    "mut": "MUT",
    "pub": "PUB",
    "ref": "REF",
    "Self": "SELF_TYPE",
    "self": "SELF_VALUE",
    "static": "STATIC",
    "struct": "STRUCT",
    "super": "SUPER",
    "trait": "TRAIT",
    "type": "TYPE",
    "union": "UNION",
    "unsafe": "UNSAFE",
    "use": "USE",
    "where": "WHERE",
    # Tipos de datos numéricos
    "i8": "I8",
    "i16": "I16",
    "i32": "I32",
    "i64": "I64",
    "i128": "I128",
    "isize": "ISIZE",
    "u8": "U8",
    "u16": "U16",
    "u32": "U32",
    "u64": "U64",
    "u128": "U128",
    "usize": "USIZE",
    "f32": "F32",
    "f64": "F64",
}

tokens_aaortizdev = (
    "IDENTIFIER",
    "INTEGER_LITERAL",
    "FLOAT_LITERAL",
    "PLUS",
    "MINUS",
    "TIMES",
    "DIVIDE",
    "MOD",
    "ASSIGN",
    "PLUS_ASSIGN",
    "MINUS_ASSIGN",
    "TIMES_ASSIGN",
    "DIVIDE_ASSIGN",
    "MOD_ASSIGN",
    "BITAND_ASSIGN",
    "BITOR_ASSIGN",
    "BITXOR_ASSIGN",
    "SHL_ASSIGN",
    "SHR_ASSIGN",
    "LBRACKET",
    "RBRACKET",
    "SEMICOLON",
    "COMMA",
    "COLON",
    "UNDERSCORE",
)

# ============================================================
# INICIO APORTE: @jonaguilera13 (Carlos Aguilera)
# ============================================================

reserved_jonathan = {
    # Estructuras de control
    "if": "IF",
    "else": "ELSE",
    "while": "WHILE",
    "for": "FOR",
    "loop": "LOOP",
    "match": "MATCH",
    "in": "IN",
    "break": "BREAK",
    "continue": "CONTINUE",
    "return": "RETURN",
    # Valores y tipo booleano
    "true": "TRUE",
    "false": "FALSE",
    "bool": "BOOL",
}

tokens_jonathan = (
    # Operadores relacionales
    "EQ",   # Equivalente
    "NE",   # Diferente
    "LT",   # menor
    "LE",   # menor igual que
    "GT",   # mayor
    "GE",   # mayor igual que
    
    # Operadores lógicos
    "AND",
    "OR",
    "NOT",

    # Paréntesis: tuplas, agrupación y llamadas
    "LPAREN", # paréntesis izquierdo
    "RPAREN", # paréntesis derecho
)

reserved_christian = {
    # TODO @ChrisPal2307: String, str, char, Vec, vec, print, println
}

tokens_christian = (
    # TODO @ChrisPal2307: Literales de cadenas, delimitadores de bloques/funciones, etc.
)

reserved = {**reserved_aaortizdev, **reserved_jonathan, **reserved_christian}
tokens = (
    tokens_aaortizdev
    + tokens_jonathan
    + tokens_christian
    + tuple(reserved.values())
)

# ============================================================
# CONTINUACIÓN APORTE: @aaortizdev (Ariel Ortiz)
# ============================================================

# Reglas de expresiones regulares simples

# Operadores de asignación compuestos
t_PLUS_ASSIGN   = r'\+='
t_MINUS_ASSIGN  = r'-='
t_TIMES_ASSIGN  = r'\*='
t_DIVIDE_ASSIGN = r'/='
t_MOD_ASSIGN    = r'%='
t_BITAND_ASSIGN = r'&='
t_BITOR_ASSIGN  = r'\|='
t_BITXOR_ASSIGN = r'\^='
t_SHL_ASSIGN    = r'<<='
t_SHR_ASSIGN    = r'>>='

# Operadores aritméticos y de asignación básica
t_PLUS   = r'\+'
t_MINUS  = r'-'
t_TIMES  = r'\*'
t_DIVIDE = r'/'
t_MOD    = r'%'
t_ASSIGN = r'='

# Símbolos para arreglos y declaraciones
t_LBRACKET  = r'\['
t_RBRACKET  = r'\]'
t_SEMICOLON = r';'
t_COMMA     = r','
t_COLON     = r':'

# --- Reglas de detección de errores léxicos en números e identificadores --- 
def t_INVALID_FLOAT(t):
    r'\d(?:_?\d)*(?:\.\d(?:_?\d)*){2,}'
    col = find_column(t.lexer.lexdata, t)
    msg = (
        f"[ERROR LÉXICO] Línea {t.lineno}, Columna {col}: "
        f"Literal numérico inválido '{t.value}' (múltiples puntos decimales)."
    )
    print(msg)
    lexical_errors.append(msg)

def t_MALFORMED_ID(t):
    r'\d(?:_?\d)*_?[a-zA-Z][a-zA-Z\d_]*'
    col = find_column(t.lexer.lexdata, t)
    msg = (
        f"[ERROR LÉXICO] Línea {t.lineno}, Columna {col}: "
        f"Identificador malformado '{t.value}' (no puede iniciar con un dígito numérico)."
    )
    print(msg)
    lexical_errors.append(msg)
    
# --- Reglas de literales numéricos válidos ---
def t_FLOAT_LITERAL(t):
    r'\d(?:_?\d)*\.\d(?:_?\d)*'
    t.value = float(t.value.replace("_", ""))
    return t 

def t_INTEGER_LITERAL(t):
    r'\d(?:_?\d)*'
    t.value = int(t.value.replace("_", ""))
    return t

# --- Identificadores y palabras reservadas ---
def t_IDENTIFIER(t):
    r'[a-zA-Z_][a-zA-Z\d_]*'
    if t.value == '_':
        t.type = "UNDERSCORE"
    else:
        t.type = reserved.get(t.value, "IDENTIFIER")
    return t

# ============================================================
# FIN APORTE: @aaortizdev (Ariel Ortiz)
# ============================================================

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

t_ignore = ' \t\r'

def t_error(t):
    col = find_column(t.lexer.lexdata, t)
    msg = (
        f"[ERROR LÉXICO] Línea {t.lineno}, Columna {col}: "
        f"Carácter no reconocido en el lenguaje '{t.value[0]}'"
    )
    print(msg)
    lexical_errors.append(msg)
    t.lexer.skip(1)

lexer = lex.lex()