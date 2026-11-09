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
    "FAT_ARROW", #Sirve para el comando match
)


# ============================================================
# INICIO APORTE: @ChrisPal2307 (Christian Palma)
# ============================================================

reserved_christian = {
    "char": "CHAR",
    "str": "STR",
}

tokens_christian = (
    "BANG",          
    "QUESTION",

    # Delimitadores de bloques y acceso
    "LBRACE",        # {
    "RBRACE",        # }
    "DOT",           # .
    "DOTDOT",        # ..
    "DOTDOTEQ",      # ..=
    "PATH_SEP",      # ::   
      
    # Operadores bitwise y referencias
    "BITAND",        # & (Referencias o AND bitwise)
    "BITOR",         # | (Patrones match o BITOR bitwise)
    "BITXOR",        # ^ (XOR bitwise)
    "SHL",           # <<
    "SHR",           # >>
    "ARROW",         # -> (Retorno de funciones)

    # Literales 
    "STRING_LITERAL", # "texto"
    "CHAR_LITERAL",   # 'c'
)

reserved = {**reserved_aaortizdev, **reserved_jonathan, **reserved_christian}
tokens = (
    tokens_aaortizdev
    + tokens_jonathan
    + tokens_christian
    + tuple(reserved.values())
)


#Antes de la definicion de "/"
def t_BLOCK_COMMENT(t):
    r'/\*'
    source = t.lexer.lexdata
    start = t.lexpos
    index = t.lexer.lexpos
    depth = 1

    while index < len(source) and depth:
        if source.startswith('/*', index):
            depth += 1
            index += 2
        elif source.startswith('*/', index):
            depth -= 1
            index += 2
        else:
            index += 1

    comment = source[start:index]
    t.lexer.lexpos = index
    t.lexer.lineno += comment.count('\n')

    if depth:
        col = find_column(source, t)
        msg = (
            f"[ERROR LÉXICO] Línea {t.lineno}, Columna {col}: "
            f"Comentario multilínea sin cerrar ('/*')."
        )
        print(msg)
        lexical_errors.append(msg)

def t_LINE_COMMENT(t):
    r'//.*'
    pass

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


def t_INVALID_BASE_LITERAL(t):
    r'0[bB][01_]*[2-9a-zA-Z]+[a-zA-Z\d_]*|0[oO][0-7_]*[89a-zA-Z]+[a-zA-Z\d_]*|0[xX][0-9a-fA-F_]*[g-zG-Z]+[a-zA-Z\d_]*'
    col = find_column(t.lexer.lexdata, t)
    msg = (
        f"[ERROR LÉXICO] Línea {t.lineno}, Columna {col}: "
        f"Literal numérico en base no válida o malformado '{t.value}'."
    )
    print(msg)
    lexical_errors.append(msg)

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
    r'(?!(?:0[bB][01_]+|0[oO][0-7_]+|0[xX][0-9a-fA-F_]+)(?![a-zA-Z\d_]))\d(?:_?\d)*(?!i8|i16|i32|i64|i128|isize|u8|u16|u32|u64|u128|usize|f32|f64\b)_?[a-zA-Z][a-zA-Z\d_]*'
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
    r'(?:0b[01_]+|0x[0-9a-fA-F_]+|0o[0-7_]+|\d(?:_?\d)*)'
    # Procesar el valor según la base
    val_str = t.value.replace("_", "")
    if val_str.startswith("0b"):
        t.value = int(val_str[2:], 2)
    elif val_str.startswith("0x"):
        t.value = int(val_str[2:], 16)
    elif val_str.startswith("0o"):
        t.value = int(val_str[2:], 8)
    else:
        t.value = int(val_str)
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

# ============================================================
# CONTINUACIÓN APORTE: @jonaguilera13 (Carlos Aguilera)
# ============================================================

#Relación de los nombres de los tokens escogidos para reconocer operadores relacionales, lógicos y paréntesis.
t_EQ = r'=='
t_NE = r'!='
t_LE = r'<='
t_GE = r'>='
t_LT = r'<'
t_GT = r'>'

t_AND = r'&&'
t_OR = r'\|\|'
t_NOT = r'!'

t_LPAREN = r'\('
t_RPAREN = r'\)'
t_FAT_ARROW = r'=>'
# ============================================================
# FIN APORTE: @jonaguilera13 (Carlos Aguilera)
# ============================================================



# ============================================================
# CONTINUACIÓN APORTE: @ChrisPal2307 (Christian Palma)
# ============================================================

# Operadores compuestos y delimitadores multicarácter
t_DOTDOTEQ  = r'\.\.='
t_DOTDOT    = r'\.\.'
t_PATH_SEP  = r'::'
t_SHL       = r'<<'
t_SHR       = r'>>'
t_ARROW     = r'->'

# Operadores de un solo carácter y delimitadores de bloques
t_BANG      = r'!'
t_QUESTION  = r'\?'
t_LBRACE    = r'\{'
t_RBRACE    = r'\}'
t_DOT       = r'\.'
t_BITAND    = r'&'
t_BITOR     = r'\|'
t_BITXOR    = r'\^'

def t_UNCLOSED_STRING(t):
    r'"([^"\\\n]|\\[^\n])*(?=\n|$)'
    col = find_column(t.lexer.lexdata, t)
    msg = (
        f"[ERROR LÉXICO] Línea {t.lineno}, Columna {col}: "
        "Cadena de texto sin cerrar (falta la comilla doble de cierre)."
    )
    print(msg)
    lexical_errors.append(msg)
    
def t_UNCLOSED_CHAR_LITERAL(t):
    r"'(?:[^'\\\n]|\\.)*(?=\n|$)"
    col = find_column(t.lexer.lexdata, t)
    msg = f"[ERROR LÉXICO] Línea {t.lineno}, Columna {col}: Literal de carácter sin cerrar."
    print(msg)
    lexical_errors.append(msg)

def t_STRING_LITERAL(t):
    r'"([^"\\]|\\.)*"'
    t.lexer.lineno += t.value.count('\n')
    return t

def t_INVALID_CHAR_LITERAL(t):
    r"''|'(?:[^'\\\n]|\\.){2,}'"
    col = find_column(t.lexer.lexdata, t)
    msg = (
        f"[ERROR LÉXICO] Línea {t.lineno}, Columna {col}: "
        f"Literal de carácter inválido {t.value!r}: debe contener exactamente un carácter."
    )
    print(msg)
    lexical_errors.append(msg)

def t_CHAR_LITERAL(t):
    r'\'([^\'\\]|\\.)\''
    return t

def t_UNSUPPORTED_BACKTICK_LITERAL(t):
    r'`[^`\n]*`'
    col = find_column(t.lexer.lexdata, t)
    msg = (
        f"[ERROR LÉXICO] Línea {t.lineno}, Columna {col}: "
        f"Literal delimitado por backticks {t.value!r} no es válido en este lenguaje; "
        "usa comillas dobles para cadenas."
    )
    print(msg)
    lexical_errors.append(msg)



# ============================================================
# FIN APORTE: @ChrisPal2307 (Christian Palma)
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