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

# ============================================================
# FIN APORTE: @aaortizdev (Ariel Ortiz)
# ============================================================
