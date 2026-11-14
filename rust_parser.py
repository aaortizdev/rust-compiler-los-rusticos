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

# --------- Declaración de variables ------------
def p_statement_var_decl(p):
    '''statement : LET mutability IDENTIFIER type_annotation ASSIGN expression SEMICOLON'''
    p[0] = ('let', p[2], p[3], p[4], p[6])

def p_mutability(p):
    '''mutability : MUT | empty'''
    p[0] = p[1] is not None

def p_type_annotation(p):
    '''type_annotation : COLON type | empty'''
    p[0] = p[2] if len(p) == 3 else None

# --------- Declaración de constantes -----------
def p_statement_const_decl(p):
    '''statement : CONST IDENTIFIER COLON type ASSIGN expression SEMICOLON'''
    p[0] = ('const', p[2], p[4], p[6])

# ------ Asignaciones simples y compuestas ------
def p_statement_assignment(p):
    '''statement : lvalue assign_op expression SEMICOLON'''
    p[0] = ('assign', p[1], p[2], p[3])

def p_lvalue(p):
    '''lvalue : IDENTIFIER | lvalue LBRACKET expression RBRACKET'''
    p[0] = ('var', p[1]) if len(p) == 2 else ('index', p[1], p[3])

def p_assign_op(p):
    '''assign_op : ASSIGN
                 | PLUS_ASSIGN
                 | MINUS_ASSIGN
                 | TIMES_ASSIGN
                 | DIVIDE_ASSIGN
                 | MOD_ASSIGN
                 | BITAND_ASSIGN
                 | BITOR_ASSIGN
                 | BITXOR_ASSIGN
                 | SHL_ASSIGN
                 | SHR_ASSIGN'''
    p[0] = p[1]

# --------- Expresiones aritmétricas ------------
# -------- Literales (valores para asignar) -----
# --- Arreglos: tipo, inicialización y acceso ---
# -------- Estructura de control while ----------
# --- Función sin parámetros y sin retorno ------

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
