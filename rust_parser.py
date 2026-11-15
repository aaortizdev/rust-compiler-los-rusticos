# ------------------------------------------------------------
# rust_parser.py
#
# Analizador sintáctico para un subconjunto de Rust usando PLY (yacc)
# ------------------------------------------------------------
import ply.yacc as yacc
from rust_lexer import tokens, lexer, find_column

syntax_errors = []


def _token_at_position(source, position):
    scan_lexer = lexer.clone()
    scan_lexer.lineno = 1
    scan_lexer.begin('INITIAL')
    scan_lexer.lexstatestack = []

    def skip_invalid_token(token):
        scan_lexer.skip(1)

    scan_lexer.lexerrorf = skip_invalid_token
    scan_lexer.input(source)
    while True:
        token = scan_lexer.token()
        if token is None or token.lexpos >= position:
            return token if token is not None and token.lexpos == position else None


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
    '''statement : primary assign_op expression SEMICOLON'''
    if p[1][0] not in ('var', 'index', 'field_access'):
        msg = "[ERROR SINTÁCTICO] La expresión no es asignable."
        print(msg)
        syntax_errors.append(msg)
    p[0] = ('assign', p[1], p[2], p[3])

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

# --- Tipo Vector: Vec<T> (soporta anidados como Vec<Vec<i32>>) ---
def p_type_vec(p):
    '''type : IDENTIFIER LT type GT'''
    if p[1] != 'Vec':
        msg = f"[ERROR SINTÁCTICO] Línea {p.lineno(1)}: Tipo genérico '{p[1]}' no soportado, se esperaba 'Vec'."
        print(msg)
        syntax_errors.append(msg)
    p[0] = ('vec_type', p[3])


def p_statement_var_decl_missing_vec_gt(p):
    '''statement : LET mutability IDENTIFIER COLON IDENTIFIER LT type ASSIGN expression SEMICOLON
                 | LET mutability IDENTIFIER COLON IDENTIFIER LT type ASSIGN expression'''
    if p[5] == 'Vec':
        token = p.slice[8]
        col = find_column(p.lexer.lexdata, token)
        msg = (
            f"[ERROR SINTÁCTICO] Línea {p.lineno(8)}, Columna {col}: "
            f"Token inesperado '{token.value}' ({token.type})."
        )
    else:
        msg = f"[ERROR SINTÁCTICO] Línea {p.lineno(5)}: Tipo genérico '{p[5]}' no soportado, se esperaba 'Vec'."
    print(msg)
    syntax_errors.append(msg)
    if len(p) == 10:
        msg = f"[ERROR SINTÁCTICO] Línea {p.lineno(1)}: Falta ';' al final de la declaración let."
        print(msg)
        syntax_errors.append(msg)
    p[0] = ('let', p[2], p[3], ('vec_type', p[7]), p[9])


# --- Inicialización con macro: vec![1, 2, 3] o vec![] ---
def p_primary_vec_macro(p):
    '''primary : IDENTIFIER NOT LBRACKET vec_elements_opt RBRACKET'''
    if p[1] != 'vec':
        msg = f"[ERROR SINTÁCTICO] Línea {p.lineno(1)}: Macro '{p[1]}!' no reconocida, se esperaba 'vec!'."
        print(msg)
        syntax_errors.append(msg)
    p[0] = ('vec', p[4])


# --- Inicialización por repetición: vec![0; 5] ---
def p_primary_vec_repeat(p):
    '''primary : IDENTIFIER NOT LBRACKET expression SEMICOLON expression RBRACKET'''
    if p[1] != 'vec':
        msg = f"[ERROR SINTÁCTICO] Línea {p.lineno(1)}: Macro '{p[1]}!' no reconocida, se esperaba 'vec!'."
        print(msg)
        syntax_errors.append(msg)
    p[0] = ('vec_repeat', p[4], p[6])


def p_vec_elements_opt(p):
    '''vec_elements_opt : vec_elements
                        | empty'''
    p[0] = p[1] if p[1] is not None else []


def p_vec_elements(p):
    '''vec_elements : expression
                    | vec_elements COMMA expression
                    | vec_elements COMMA'''
    if len(p) == 2:
        p[0] = [p[1]]
    elif len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = p[1]


def p_vec_elements_missing_comma(p):
    '''vec_elements : vec_elements expression'''
    token = _token_at_position(p.lexer.lexdata, p.lexpos(2))
    if token is None:
        raise ValueError(
            f"No se encontró un token en la posición {p.lexpos(2)} al reportar "
            "un elemento vec! sin coma."
        )
    col = find_column(p.lexer.lexdata, token)
    msg = (
        f"[ERROR SINTÁCTICO] Línea {token.lineno}, Columna {col}: "
        f"Token inesperado '{token.value}' ({token.type})."
    )
    print(msg)
    syntax_errors.append(msg)
    p[0] = p[1] + [p[2]]


# --- Constructores asociados: Vec::new(), Vec::with_capacity(10) ---
def p_primary_assoc_call(p):
    '''primary : IDENTIFIER PATH_SEP IDENTIFIER LPAREN call_arguments_opt RPAREN'''
    p[0] = ('assoc_call', p[1], p[3], p[5])


# --- Métodos de instancia: v.push(10), v.pop(), v.len(), v.remove(0) ---
def p_method_call(p):
    '''method_call : primary DOT IDENTIFIER LPAREN call_arguments_opt RPAREN'''
    p[0] = ('method_call', p[1], p[3], p[5])


def p_method_call_missing_mut_borrow(p):
    '''method_call : primary DOT IDENTIFIER LPAREN MUT IDENTIFIER RPAREN'''
    if p[3] == 'read_line':
        token = p.slice[5]
        col = find_column(p.lexer.lexdata, token)
        msg = (
            f"[ERROR SINTÁCTICO] Línea {p.lineno(5)}, Columna {col}: "
            f"Token inesperado '{token.value}' ({token.type})."
        )
    else:
        msg = f"[ERROR SINTÁCTICO] Línea {p.lineno(5)}: El argumento 'mut {p[6]}' debe escribirse como '&mut {p[6]}'."
    print(msg)
    syntax_errors.append(msg)
    p[0] = ('method_call', p[1], p[3], [('var', p[6])])


def p_primary_method_call(p):
    '''primary : method_call'''
    p[0] = p[1]


def p_statement_method_call(p):
    '''statement : method_call SEMICOLON'''
    p[0] = ('expr_stmt', p[1])

def p_statement_for(p):
    '''statement : FOR IDENTIFIER IN for_iterator block'''
    p[0] = ('for', p[2], p[4], p[5])

def p_for_iterator(p):
    '''for_iterator : expression
                    | expression DOTDOT expression
                    | expression DOTDOTEQ expression'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ('range', p[2], p[1], p[3])


def p_statement_for_missing_in(p):
    '''statement : FOR IDENTIFIER for_iterator block'''
    token = _token_at_position(p.lexer.lexdata, p.lexpos(3))
    if token is None:
        raise ValueError(
            f"No se encontró un token en la posición {p.lexpos(3)} al reportar "
            "un ciclo for sin 'in'."
        )
    col = find_column(p.lexer.lexdata, token)
    msg = (
        f"[ERROR SINTÁCTICO] Línea {token.lineno}, Columna {col}: "
        f"Token inesperado '{token.value}' ({token.type})."
    )
    print(msg)
    syntax_errors.append(msg)
    p[0] = ('for', p[2], p[3], p[4])


def p_statement_fn_no_params_return(p):
    '''statement : FN IDENTIFIER LPAREN RPAREN ARROW type block'''
    p[0] = ('fn', p[2], [], p[6], p[7])


def p_statement_fn_params_return(p):
    '''statement : FN IDENTIFIER LPAREN fn_parameters RPAREN ARROW type block'''
    p[0] = ('fn', p[2], p[4], p[7], p[8])


def p_statement_fn_missing_return_type(p):
    '''statement : FN IDENTIFIER LPAREN RPAREN ARROW block
                 | FN IDENTIFIER LPAREN fn_parameters RPAREN ARROW block'''
    if len(p) == 7:
        name, parameters, body_index, body = p[2], [], 6, p[6]
    else:
        name, parameters, body_index, body = p[2], p[4], 7, p[7]
    token = p.slice[body_index]
    col = find_column(p.lexer.lexdata, token)
    msg = (
        f"[ERROR SINTÁCTICO] Línea {p.lineno(body_index)}, Columna {col}: "
        "Token inesperado '{' (LBRACE)."
    )
    print(msg)
    syntax_errors.append(msg)
    p[0] = ('fn', name, parameters, None, body)


def p_statement_return(p):
    '''statement : RETURN expression SEMICOLON
                 | RETURN SEMICOLON'''
    p[0] = ('return', p[2]) if len(p) == 4 else ('return', None)


def p_statement_print_macro(p):
    '''statement : IDENTIFIER NOT LPAREN call_arguments_opt RPAREN SEMICOLON'''
    if p[1] not in ('print', 'println'):
        msg = f"[ERROR SINTÁCTICO] Línea {p.lineno(1)}: Macro de impresión '{p[1]}!' no reconocida."
        print(msg)
        syntax_errors.append(msg)
    p[0] = ('print_macro', p[1], p[4])


def p_statement_use(p):
    '''statement : USE use_path SEMICOLON
                 | USE use_path'''
    p[0] = ('use', p[2])
    if len(p) == 3:
        msg = f"[ERROR SINTÁCTICO] Línea {p.lineno(1)}: Falta ';' al final de la declaración use."
        print(msg)
        syntax_errors.append(msg)


def p_statement_missing_semicolon(p):
    '''statement : LET mutability IDENTIFIER type_annotation ASSIGN expression
                 | CONST IDENTIFIER COLON type ASSIGN expression
                 | primary assign_op expression
                 | function_call
                 | method_call
                 | RETURN expression
                 | RETURN
                 | IDENTIFIER NOT LPAREN call_arguments_opt RPAREN'''
    line = p.lineno(1) or p.lexer.lineno
    msg = f"[ERROR SINTÁCTICO] Línea {line}: Falta ';' al final de la instrucción."
    print(msg)
    syntax_errors.append(msg)
    p[0] = ('invalid_statement',)


def p_use_path(p):
    '''use_path : IDENTIFIER
                | path'''
    p[0] = [p[1]] if isinstance(p[1], str) else p[1]


def p_path(p):
    '''path : IDENTIFIER PATH_SEP IDENTIFIER
            | path PATH_SEP IDENTIFIER'''
    p[0] = [p[1], p[3]] if len(p) == 4 and isinstance(p[1], str) else p[1] + [p[3]]


def p_primary_path_call(p):
    '''primary : path PATH_SEP IDENTIFIER LPAREN call_arguments_opt RPAREN'''
    p[0] = ('path_call', p[1] + [p[3]], p[5])


def p_primary_mut_borrow(p):
    '''primary : BITAND MUT primary'''
    p[0] = ('borrow_mut', p[3])


def p_statement_impl(p):
    '''statement : IMPL IDENTIFIER LBRACE impl_methods_opt RBRACE'''
    p[0] = ('impl', p[2], p[4])


def p_impl_methods_opt(p):
    '''impl_methods_opt : impl_methods
                        | empty'''
    p[0] = p[1] if p[1] is not None else []


def p_impl_methods(p):
    '''impl_methods : impl_method
                    | impl_methods impl_method'''
    p[0] = [p[1]] if len(p) == 2 else p[1] + [p[2]]


def p_impl_method(p):
    '''impl_method : FN IDENTIFIER LPAREN impl_method_parameters_opt RPAREN impl_return_type block
                   | PUB FN IDENTIFIER LPAREN impl_method_parameters_opt RPAREN impl_return_type block'''
    if len(p) == 8:
        p[0] = ('method', p[2], p[4], p[6], p[7], False)
    else:
        p[0] = ('method', p[3], p[5], p[7], p[8], True)


def p_impl_method_missing_return_type(p):
    '''impl_method : FN IDENTIFIER LPAREN impl_method_parameters_opt RPAREN ARROW block
                   | PUB FN IDENTIFIER LPAREN impl_method_parameters_opt RPAREN ARROW block'''
    if len(p) == 8:
        name, parameters, body_index, body, is_public = p[2], p[4], 7, p[7], False
    else:
        name, parameters, body_index, body, is_public = p[3], p[5], 8, p[8], True
    token = p.slice[body_index]
    col = find_column(p.lexer.lexdata, token)
    msg = (
        f"[ERROR SINTÁCTICO] Línea {p.lineno(body_index)}, Columna {col}: "
        "Token inesperado '{' (LBRACE)."
    )
    print(msg)
    syntax_errors.append(msg)
    p[0] = ('method', name, parameters, None, body, is_public)


def p_impl_method_parameters_opt(p):
    '''impl_method_parameters_opt : impl_method_parameters
                                  | empty'''
    p[0] = p[1] if p[1] is not None else []


def p_impl_method_parameters(p):
    '''impl_method_parameters : impl_method_parameter
                              | impl_method_parameters COMMA impl_method_parameter
                              | impl_method_parameters COMMA'''
    if len(p) == 2:
        p[0] = [p[1]]
    elif len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = p[1]


def p_impl_method_parameter(p):
    '''impl_method_parameter : fn_parameter
                             | impl_receiver'''
    p[0] = p[1]


def p_impl_receiver(p):
    '''impl_receiver : SELF_VALUE
                     | BITAND SELF_VALUE
                     | BITAND MUT SELF_VALUE
                     | MUT SELF_VALUE'''
    if p.slice[1].type == 'SELF_VALUE':
        receiver = 'self'
    elif p.slice[1].type == 'BITAND':
        receiver = '&mut self' if len(p) == 4 else '&self'
    else:
        receiver = 'mut self'
    p[0] = ('receiver', receiver)


def p_impl_return_type(p):
    '''impl_return_type : ARROW type
                        | empty'''
    p[0] = p[2] if len(p) == 3 else None


def p_type_self(p):
    '''type : SELF_TYPE'''
    p[0] = ('named_type', p[1])


def p_primary_self_value(p):
    '''primary : SELF_VALUE'''
    p[0] = ('var', p[1])

# ===============================================
# FIN APORTE: @ChrisPal2307 (Christian Palma)
# ===============================================

def find_unclosed_delimiter_errors(source):
    delimiter_pairs = {
        'LBRACE': ('RBRACE', '}'),
        'LPAREN': ('RPAREN', ')'),
        'LBRACKET': ('RBRACKET', ']'),
    }
    closing_delimiters = {
        closing: opening
        for opening, (closing, _) in delimiter_pairs.items()
    }
    scan_lexer = lexer.clone()
    scan_lexer.lineno = 1
    scan_lexer.begin('INITIAL')
    scan_lexer.lexstatestack = []

    def skip_invalid_token(token):
        scan_lexer.skip(1)

    scan_lexer.lexerrorf = skip_invalid_token
    scan_lexer.input(source)

    stack = []
    errors = []
    while True:
        token = scan_lexer.token()
        if token is None:
            break
        if token.type in delimiter_pairs:
            stack.append(token)
            continue
        if token.type not in closing_delimiters:
            continue

        matching_opening = closing_delimiters[token.type]
        matching_index = next(
            (index for index in range(len(stack) - 1, -1, -1)
             if stack[index].type == matching_opening),
            None,
        )
        if matching_index is None:
            continue

        for opener in reversed(stack[matching_index + 1:]):
            expected_closing = delimiter_pairs[opener.type][1]
            col = find_column(source, opener)
            errors.append(
                f"[ERROR SINTÁCTICO] Línea {opener.lineno}, Columna {col}: "
                f"Falta '{expected_closing}' para cerrar '{opener.value}'."
            )
        del stack[matching_index:]

    for opener in reversed(stack):
        expected_closing = delimiter_pairs[opener.type][1]
        col = find_column(source, opener)
        errors.append(
            f"[ERROR SINTÁCTICO] Línea {opener.lineno}, Columna {col}: "
            f"Falta '{expected_closing}' para cerrar '{opener.value}'."
        )
    return errors


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
