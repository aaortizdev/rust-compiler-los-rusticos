// Funciones auxiliares válidas para probar llamadas y retornos
fn sumar(a: i32, b: i32) -> i32 {
    a + b
}

fn saludar(nombre: &str, veces: i32) {
    let x = veces;
}

// --- REGLA 1: RETORNOS ---

// Error 1: Return explícito con tipo incompatible (espera i32, recibe &str)
fn retorno_invalido_explicit() -> i32 {
    return "texto";
}

// Error 2: Expresión final implícita con tipo incompatible (espera bool, recibe i32)
fn retorno_invalido_implicito() -> bool {
    let a = 10;
    a + 5
}

// Error 3: Función sin tipo de retorno intenta devolver un valor
fn sin_retorno_con_valor() {
    return 42;
}

// Error 4: Función sin tipo de retorno termina con expresión sin ';'
fn sin_retorno_expresion_final() {
    let x = 10;
    x + 1
}

// Error 5: Función declara retorno -> i32 pero hace 'return;' vacío
fn retorno_vacio_esperando_tipo() -> i32 {
    return;
}

// Error 6: Función declara retorno -> i32 pero termina en sentencia con ';' (no devuelve nada)
fn falta_retorno_final() -> i32 {
    let x = 20;
}

// --- REGLA 2: LLAMADAS A FUNCIONES ---

fn main() {
    // Error 7: Llamada a una función que no existe
    let a = funcion_inexistente(1, 2);

    // Error 8: Cantidad incorrecta de argumentos (espera 2, recibe 1)
    let b = sumar(10);

    // Error 9: Tipo de argumento incorrecto (arg 2 espera i32, recibe bool)
    saludar("Christian", true);
}