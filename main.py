import os
from datetime import datetime
from rust_lexer import lexer, lexical_errors, find_column

def analizar_archivo_y_generar_log(ruta_archivo_rs, usuario_git):
    lexical_errors.clear()
    lexer.lineno = 1

    with open(ruta_archivo_rs, "r", encoding="utf-8") as f:
        codigo_fuente = f.read()

    lexer.input(codigo_fuente)

    os.makedirs("logs", exist_ok=True)

    ahora = datetime.now()
    fecha_hora = ahora.strftime("%d-%m-%Y-%Hh%M")
    nombre_log = f"logs/lexico-{usuario_git}-{fecha_hora}.txt"

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
    
if __name__ == "__main__":
    analizar_archivo_y_generar_log("algoritmos/algoritmo3_aaortizdev.rs", "aaortizdev")
    # analizar_archivo_y_generar_log("algoritmos/algoritmo#_jonaguilera13.rs", "jonaguilera13")
    # analizar_archivo_y_generar_log("algoritmos/algoritmo#_ChrisPal2307.rs", "ChrisPal2307")
