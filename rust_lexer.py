# ------------------------------------------------------------
# rust_lexer.py
#
# tokenizer
# ------------------------------------------------------------
import ply.lex as lex

#Palabras reservadas para declaraciones 
reserved = {
    "as": "AS",
    "async": "ASYNC",
    "await": "AWAIT",
    "break": "BREAK",
    "continue": "CONTINUE",
    "let": "LET",
    "mut": "MUT",
    "const": "CONST",
    "crate": "CRATE",
    "dyn": "DYN",
    "if": "IF",
    "else": "ELSE",
    "enum": "ENUM",
    "extern": "EXTERN",
    "true": "TRUE",
    "false": "FALSE",
    "fn": "FN",
    "for": "FOR",
    "while": "WHILE",
    "loop": "LOOP",
    "in": "IN",
    "struct": "STRUCT",
    "return": "RETURN",
    "impl": "IMPL",
    "match": "MATCH",
    "mod": "MOD",
    "move": "MOVE",
    "pub": "PUB",
    "ref": "REF",
    "Self": "SELF_TYPE",
    "self": "SELF_VALUE",
    "static": "STATIC",
    "super": "SUPER",
    "trait": "TRAIT",
    "type": "TYPE",
    "union": "UNION",
    "unsafe": "UNSAFE",
    "use": "USE",
    "where": "WHERE",
}
