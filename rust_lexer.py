# ------------------------------------------------------------
# rust_lexer.py
#
# Analizador léxico para un subconjunto de Rust usando PLY
# ------------------------------------------------------------
import ply.lex as lex

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
    "mod": "MOD",
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
    # Identificadores
    'ID_STANDARD', 
    'ID_CONST', 
    'ID_TYPE',
    # Literales númericos 
    "INTEGER_LITERAL", 
    "FLOAT_LITERAL",
    # Operadores Aritméticos
    "PLUS",
    "MINUS",
    "TIMES",
    "DIVIDE",
    "MOD",
    # Operadores de Asignación
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
    # Símbolos para arreglos y declaraciones
    "LBRACKET", 
    "RBRACKET", 
    "SEMICOLON", 
    "COMMA",
    "COLON"
)

# ============================================================
# ESPACIO PARA @jonaguilera13 Y @ChrisPal2307
# ============================================================

reserved_jonathan = {
    # TODO @jonaguilera13: if, else, while, for, loop, match, in, break, continue, return, true, false, bool
}

reserved_christian = {
    # TODO @ChrisPal2307: String, str, char, Vec, vec, print, println
}

reserved = {**reserved_aaortizdev, **reserved_jonathan, **reserved_christian}
tokens = tokens_aaortizdev + tuple(reserved.values())

# ============================================================
# FIN APORTE: @aaortizdev (Ariel Ortiz)
# ============================================================
