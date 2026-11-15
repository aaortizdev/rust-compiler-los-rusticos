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

precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('nonassoc', 'EQ', 'NE', 'LT', 'LE', 'GT', 'GE'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE', 'MOD'),
    ('right', 'NOT', 'UMINUS'),
)

def p_program(p):
    '''program : statement_list'''
    p[0] = ('program', p[1])


def p_statement_list(p):
    '''statement_list : statement_list statement
                      | statement'''
    p[0] = p[1] + [p[2]] if len(p) == 3 else [p[1]]


def p_block(p):
    '''block : LBRACE statement_list RBRACE
             | LBRACE RBRACE'''
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
    '''mutability : MUT
                  | empty'''
    p[0] = p[1] is not None

def p_type_annotation(p):
    '''type_annotation : COLON type
                       | empty'''
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
    '''lvalue : IDENTIFIER
              | lvalue LBRACKET expression RBRACKET'''
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

# ----------- Expresiones aritmétricas ----------
def p_expression_binop(p):
    '''expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression
                  | expression MOD expression'''
    p[0] = ('binop', p[2], p[1], p[3])

def p_expression_uminus(p):
    '''expression : MINUS expression %prec UMINUS'''
    p[0] = ('neg', p[2])

def p_expression_primary(p):
    '''expression : primary '''
    p[0] = p[1]

def p_primary_group(p):
    '''primary : LPAREN expression RPAREN'''
    p[0] = p[2]

# -------- Literales (valores para asignar) -----
def p_primary_literal(p):
    '''primary : INTEGER_LITERAL
               | FLOAT_LITERAL
               | STRING_LITERAL
               | CHAR_LITERAL
               | TRUE
               | FALSE'''
    p[0] = ('lit', p[1])

def p_primary_identifier(p):
    '''primary : IDENTIFIER'''
    p[0] = ('var', p[1])

# --- Arreglos: tipo, inicialización y acceso ---
def p_type_array(p):
    '''type : LBRACKET type SEMICOLON expression RBRACKET'''
    p[0] = ('array_type', p[2], p[4])

def p_primary_array_literal(p):
    '''primary : LBRACKET array_elements RBRACKET'''
    p[0] = ('array', p[2])

def p_array_elements(p):
    '''array_elements : array_elements COMMA expression
                      | expression'''
    p[0] = p[1] + [p[3]] if len(p) == 4 else [p[1]]

def p_primary_array_access(p):
    '''primary : primary LBRACKET expression RBRACKET'''
    p[0] = ('index', p[1], p[3])

# -------- Estructura de control while ----------
def p_statement_while(p):
    '''statement : WHILE expression block'''
    p[0] = ('while', p[2], p[3])

# --- Función sin parámetros y sin retorno ------
def p_statement_fn_no_params(p):
    '''statement : FN IDENTIFIER LPAREN RPAREN block'''
    p[0] = ('fn', p[2], p[5])

# ===============================================
# FIN APORTE: @aaortizdev (Ariel Ortiz)
# ===============================================

# ===============================================
# INICIO APORTE: @jonaguilera13 (Carlos Aguilera)
# ===============================================

#Expresiones booleanas y relacionales
def p_expression_logical_relational(p):
    '''expression : expression OR expression
                | expression AND expression
                | expression EQ expression
                | expression NE expression
                | expression LT expression
                | expression LE expression
                | expression GT expression
                | expression GE expression'''
    p[0] = ('binop', p[2], p[1], p[3])


def p_expression_not(p):
    '''expression : NOT expression'''
    p[0] = ('not', p[2])


#Tuplas: declaración, tipo y acceso
def p_type_tuple(p):
    '''type : LPAREN tuple_type_elements RPAREN
            | LPAREN RPAREN'''
    p[0] = ('tuple_type', p[2] if len(p) == 4 else [])


def p_tuple_type_elements(p):
    '''tuple_type_elements : type COMMA tuple_type_tail'''
    p[0] = [p[1]] + p[3]


def p_tuple_type_tail(p):
    '''tuple_type_tail : type
                    | type COMMA tuple_type_tail
                    | empty'''
    if len(p) == 2:
        p[0] = [] if p[1] is None else [p[1]]
    else:
        p[0] = [p[1]] + p[3]


def p_primary_tuple(p):
    '''primary : LPAREN expression COMMA tuple_expr_tail RPAREN
                | LPAREN RPAREN'''
    p[0] = ('tuple', [p[2]] + p[4] if len(p) == 6 else [])

def p_tuple_expr_tail(p):
    '''tuple_expr_tail : expression
                    | expression COMMA tuple_expr_tail
                    | empty'''
    if len(p) == 2:
        p[0] = [] if p[1] is None else [p[1]]
    else:
        p[0] = [p[1]] + p[3]


def p_primary_field_or_tuple_access(p):
    '''primary : primary DOT INTEGER_LITERAL
            | primary DOT IDENTIFIER'''
    p[0] = ('field_access', p[1], p[3])


def p_lvalue_field_or_tuple_access(p):
    '''lvalue : lvalue DOT INTEGER_LITERAL
            | lvalue DOT IDENTIFIER'''
    p[0] = ('field_access', p[1], p[3])

# if / else
def p_statement_if(p):
    '''statement : if_statement'''
    p[0] = p[1]

def p_if_statement(p):
    '''if_statement : IF expression block else_clause'''
    p[0] = ('if', p[2], p[3], p[4])


def p_else_clause(p):
    '''else_clause : ELSE block
                | ELSE if_statement
                | empty'''
    p[0] = p[2] if len(p) == 3 else None

#Estructura para match (extra)
def p_match_expr(p):
    '''match_expr : MATCH expression LBRACE match_arms_opt RBRACE'''
    p[0] = ('match', p[2], p[4])


def p_statement_match(p):
    '''statement : match_expr
                | match_expr SEMICOLON'''
    p[0] = p[1]


def p_primary_match(p):
    '''primary : match_expr'''
    p[0] = p[1]


def p_match_arms_opt(p):
    '''match_arms_opt : match_arms
                    | empty'''
    p[0] = p[1] if p[1] is not None else []


def p_match_arms(p):
    '''match_arms : match_arm
                | match_arms COMMA match_arm
                | match_arms COMMA
                | match_arms match_arm_block'''
    if len(p) == 2:
        p[0] = [p[1]]
    elif len(p) == 4:
        p[0] = p[1] + [p[3]]
    elif p.slice[2].type == 'match_arm_block':
        p[0] = p[1] + [p[2]]
    else:
        p[0] = p[1]


def p_match_arm(p):
    '''match_arm : match_arm_block
                | match_pattern FAT_ARROW expression'''
    p[0] = p[1] if len(p) == 2 else ('match_arm', p[1], p[3])


def p_match_arm_block(p):
    '''match_arm_block : match_pattern FAT_ARROW block'''
    p[0] = ('match_arm', p[1], p[3])


def p_match_pattern(p):
    '''match_pattern : INTEGER_LITERAL
                    | FLOAT_LITERAL
                    | CHAR_LITERAL
                    | STRING_LITERAL
                    | TRUE
                    | FALSE
                    | UNDERSCORE
                    | IDENTIFIER
                    | MINUS INTEGER_LITERAL'''
    if len(p) == 3:
        p[0] = ('pattern_literal', -p[2])
    else:
        p[0] = ('wildcard',) if p.slice[1].type == 'UNDERSCORE' else ('pattern', p[1])

#Función con parámetros y sin retorno.
def p_statement_fn_params(p):
    '''statement : FN IDENTIFIER LPAREN fn_parameters RPAREN block'''
    p[0] = ('fn', p[2], p[4], p[6])


def p_fn_parameters(p):
    '''fn_parameters : fn_parameter
                    | fn_parameters COMMA fn_parameter
                    | fn_parameters COMMA'''
    if len(p) == 2:
        p[0] = [p[1]]
    elif len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = p[1]


def p_fn_parameter(p):
    '''fn_parameter : IDENTIFIER COLON type
                    | MUT IDENTIFIER COLON type'''
    p[0] = ('param', p[1], p[3], False) if len(p) == 4 else ('param', p[2], p[4], True)


# Para poder utilizar las funciones definidas.
def p_function_call(p):
    '''function_call : IDENTIFIER LPAREN call_arguments_opt RPAREN'''
    p[0] = ('call', p[1], p[3])


def p_call_arguments_opt(p):
    '''call_arguments_opt : call_arguments
                    | empty'''
    p[0] = p[1] if p[1] is not None else []


def p_call_arguments(p):
    '''call_arguments : expression
                | call_arguments COMMA expression
                | call_arguments COMMA'''
    if len(p) == 2:
        p[0] = [p[1]]
    elif len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = p[1]


def p_primary_function_call(p):
    '''primary : function_call'''
    p[0] = p[1]


def p_statement_function_call(p):
    '''statement : function_call SEMICOLON'''
    p[0] = ('expr_stmt', p[1])

#struct: definición y propiedades
def p_statement_struct(p):
    '''statement : STRUCT IDENTIFIER LBRACE struct_fields_opt RBRACE
                | PUB STRUCT IDENTIFIER LBRACE struct_fields_opt RBRACE'''
    if len(p) == 6:
        p[0] = ('struct', p[2], p[4], False)
    else:
        p[0] = ('struct', p[3], p[5], True)


def p_struct_fields_opt(p):
    '''struct_fields_opt : struct_fields
                    | empty'''
    p[0] = p[1] if p[1] is not None else []


def p_struct_fields(p):
    '''struct_fields : struct_field
                    | struct_fields COMMA struct_field
                    | struct_fields COMMA'''
    if len(p) == 2:
        p[0] = [p[1]]
    elif len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = p[1]


def p_struct_field(p):
    '''struct_field : field_visibility IDENTIFIER COLON type'''
    p[0] = ('field', p[2], p[4], p[1])


def p_field_visibility(p):
    '''field_visibility : PUB
                    | empty'''
    p[0] = p[1] is not None


def p_type_struct_name(p):
    '''type : IDENTIFIER'''
    p[0] = ('named_type', p[1])

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
