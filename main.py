import argparse
import os
import re
from contextlib import redirect_stdout
from datetime import datetime
from io import StringIO
import rust_parser
import rust_semantic
from rust_lexer import lexer, lexical_errors, find_column

def analizar_archivo_y_generar_log(ruta_archivo_rs, usuario_git):
    lexical_errors.clear()
    lexer.lineno = 1

    with open(ruta_archivo_rs, "r", encoding="utf-8") as f:
        codigo_fuente = f.read()

    lexer.input(codigo_fuente)

    os.makedirs("logs/lexico", exist_ok=True)

    ahora = datetime.now()
    fecha_hora = ahora.strftime("%d-%m-%Y-%Hh%M")
    nombre_log = f"logs/lexico/lexico-{usuario_git}-{fecha_hora}.txt"

    lineas_log = []
    lineas_log.append(f"--- Log de análisis léxico ({usuario_git}) ---")
    lineas_log.append(f"Archivo analizado: {ruta_archivo_rs}")
    lineas_log.append(f"Fecha y Hora: {ahora.strftime('%d/%m/%Y %H:%M:%S')}\n")
    lineas_log.append("--- Tokens reconocidos ---")

    while True:
        tok = lexer.token()
        if not tok:
            break
        col = find_column(codigo_fuente, tok)
        lineas_log.append(
            f"Token(tipo='{tok.type}', valor='{tok.value}', línea={tok.lineno}, columna={col})"
        )

    lineas_log.append("\n--- Errores léxicos detectados ---")
    if lexical_errors:
        for err in lexical_errors:
            lineas_log.append(err)
    else:
        lineas_log.append("Ningún error léxico detectado.")
    
    contenido_final = "\n".join(lineas_log)

    with open(nombre_log, "w", encoding="utf-8") as log_file:
        log_file.write(contenido_final)
    
    print(f"\n[OK] Log generado exitosamente en: {nombre_log}")

def run_parser(path, git_user="ChrisPal2307"):
    with open(path, encoding="utf-8") as f:
        data = f.read()

    rust_parser.syntax_errors.clear()
    rust_parser.lexer.lineno = 1
    parser_output = StringIO()
    with redirect_stdout(parser_output):
        rust_parser.parser.parse(data, lexer=rust_parser.lexer, tracking=True)
    for error in rust_parser.find_unclosed_delimiter_errors(data):
        if error not in rust_parser.syntax_errors:
            rust_parser.syntax_errors.append(error)

    def error_position(error):
        match = re.search(r"Línea (\d+)(?:, Columna (\d+))?", error)
        if match is None:
            return float("inf"), 0
        return int(match.group(1)), int(match.group(2) or 0)

    rust_parser.syntax_errors.sort(key=error_position)
    for output_line in parser_output.getvalue().splitlines():
        if output_line and not output_line.startswith("[ERROR SINTÁCTICO]"):
            print(output_line)
    for error in rust_parser.syntax_errors:
        print(error)

    os.makedirs("logs/sintactico", exist_ok=True)
    ahora = datetime.now()
    log_path = f"logs/sintactico/sintactico-{git_user}-{ahora.strftime('%Y%m%d-%Hh%M')}.txt"

    lineas = [
        f"--- Log de análisis sintáctico ({git_user}) ---",
        f"Archivo analizado: {path}",
        f"Fecha y Hora: {ahora.strftime('%d/%m/%Y %H:%M:%S')}\n",
        "--- Errores sintácticos detectados ---",
    ]
    lineas += rust_parser.syntax_errors or ["Ningún error sintáctico detectado."]

    with open(log_path, "w", encoding="utf-8") as log:
        log.write("\n".join(lineas))
    print(f"[OK] Log generado en: {log_path}")

CARPETA_LOGS_SEMANTICO = os.path.join("logs", "semantico")

def run_semantic(path, git_user="aaortizdev"):
    with open(path, encoding="utf-8") as f:
        data = f.read()

    # 1. Análisis sintáctico para obtener el árbol (sin imprimir sus mensajes)
    rust_parser.syntax_errors.clear()
    rust_parser.lexer.lineno = 1
    with redirect_stdout(StringIO()):
        ast = rust_parser.parser.parse(data, lexer=rust_parser.lexer, tracking=True)
    errores_sintacticos = len(rust_parser.syntax_errors)

    # 2. Análisis semántico sobre el árbol
    errores = rust_semantic.analizar(ast, data)

    for error in errores:
        print(error)

    ahora = datetime.now()
    os.makedirs(CARPETA_LOGS_SEMANTICO, exist_ok=True)
    log_path = os.path.join(
        CARPETA_LOGS_SEMANTICO,
        f"semantico-{git_user}-{ahora.strftime('%d%m%Y-%Hh%M')}.txt",
    )

    lineas = [
        f"--- Log de análisis semántico ({git_user}) ---",
        f"Archivo analizado: {path}",
        f"Fecha y Hora: {ahora.strftime('%d/%m/%Y %H:%M:%S')}\n",
    ]
    if ast is None:
        lineas.append("[AVISO] No se pudo construir el árbol sintáctico; "
                      "corrija los errores sintácticos para ejecutar el análisis semántico.\n")
    elif errores_sintacticos:
        lineas.append(f"[AVISO] El archivo tiene {errores_sintacticos} error(es) sintáctico(s); "
                      "el análisis semántico puede estar incompleto.\n")
    lineas.append("--- Errores semánticos detectados ---")
    lineas += errores or ["Ningún error semántico detectado."]

    with open(log_path, "w", encoding="utf-8") as log:
        log.write("\n".join(lineas))
    print(f"[OK] Log generado en: {log_path}")
    
if __name__ == "__main__":
    argumentos = argparse.ArgumentParser(description="Analizador de Rust con PLY")
    argumentos.add_argument("modo", choices=["lexico", "sintactico", "semantico"])
    argumentos.add_argument("archivo", help="Ruta del archivo .rs a analizar")
    argumentos.add_argument("usuario", help="Usuario de Git para el nombre del log")
    args = argumentos.parse_args()

    if args.modo == "lexico":
        analizar_archivo_y_generar_log(args.archivo, args.usuario)
    elif args.modo == "sintactico":
        run_parser(args.archivo, args.usuario)
    else:
        run_semantic(args.archivo, args.usuario)
