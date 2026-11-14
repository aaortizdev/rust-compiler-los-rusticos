# ------------------------------------------------------------
# rust_parser.py
#
# Analizador sintáctico para un subconjunto de Rust usando PLY (yacc)
# ------------------------------------------------------------
import ply.yacc as yacc
from rust_lexer import tokens, lexer, find_column

syntax_errors = []

# ==================
# REGLAS COMPARTIDAS
# ==================

# Precedencia: de menor a mayor

# Carlos agrega aquí arriba OR, AND, relacionales;
# Christian agrega lo suyo si aplica.

precedence = (
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE', 'MOD'),
    ('right', 'UMINUS'),
)

def p_program(p):
    '''program : statement_list'''
    p[0] = ('program', p[1])


def p_statement_list(p):
    '''statement_list : statement_list statement | statement'''
    p[0] = p[1] + [p[2]] if len(p) == 3 else [p[1]]


def p_block(p):
    '''block : LBRACE statement_list RBRACE | LBRACE RBRACE'''
    p[0] = ('block', p[2] if len(p) == 4 else [])


def p_empty(p):
    '''empty :'''
    p[0] = None

def p_type_primitive(p):
    '''type : I8
            | I16
            | I32
            | I64
            | I128
            | ISIZE
            | U8
            | U16
            | U32
            | U64
            | U128
            | USIZE
            | F32
            | F64
            | BOOL
            | CHAR
            | STR
            | BITAND STR'''
    p[0] = ('type', ''.join(str(x) for x in p[1:]))
    
# ===============================================
# INICIO APORTE: @aaortizdev (Ariel Ortiz)
# ===============================================

# ===============================================
# FIN APORTE: @aaortizdev (Ariel Ortiz)
# ===============================================

# ===============================================
# INICIO APORTE: @jonaguilera13 (Carlos Aguilera)
# ===============================================

# ===============================================
# FIN APORTE: @jonaguilera13 (Carlos Aguilera)
# ===============================================

# ===============================================
# INICIO APORTE: @ChrisPal2307 (Christian Palma)
# ===============================================

# ===============================================
# FIN APORTE: @ChrisPal2307 (Christian Palma)
# ===============================================

def p_error(p):
    if p:
        col = find_column(p.lexer.lexdata, p)
        msg = (
            f"[ERROR SINTÁCTICO] Línea {p.lineno}, Columna {col}: "
            f"Token inesperado '{p.value}' ({p.type})."
        )
    else:
        msg = "[ERROR SINTÁCTICO] Fin de archivo inesperado (falta cerrar una instrucción o bloque)."
    print(msg)
    syntax_errors.append(msg)


parser = yacc.yacc(write_tables=False, debug=False)
