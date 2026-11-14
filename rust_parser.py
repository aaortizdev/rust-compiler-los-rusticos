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
    p[0] = ('program', p[1])

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
