// Declaraciones, asignaciones, expresiones, arreglos, while y funciones.

const MAX: i32 = 100;
const PI: f64 = 3.14159;
const SALUDO: &str = "Hola";

// ---- Variables con distintos tipos ----
let a = 10;
let mut b: i32 = 20;
let precio: f64 = 15.75;
let activo: bool = true;
let letra: char = 'x';
let texto: &str = "Rust";
let nombre: str = "Ariel";

// ---- Asignaciones simples y compuestas ----
b = a + 5;
b += 3;
b -= 1;
b *= 2;
b /= 4;
b %= 7;
b <<= 1;
b >>= 1;
b &= 3;
b |= 4;
b ^= 5;

// ---- Expresiones aritméticas con precedencia ----
let r1 = a + b * 2 - 3;
let r2 = (a + b) * (a - b) / 2 % 5;
let r3 = -a + -(b * 2);
let r4: f64 = 3.5 * 2.0 + 1.25;
let verdadero = false;

// ---- Arreglos ----
let numeros: [i32; 5] = [1, 2, 3, 4, 5];
let matriz: [[i32; 2]; 2] = [[1, 2], [3, 4]];
let primero = numeros[0];
let suma = numeros[0] + numeros[1] * 2;
numeros[1] = primero + 10;
numeros[2] += numeros[0] * 2;
matriz[0][1] = 9;

// ---- Estructura de control while ----
let mut contador = 0;
while activo {
    contador += 1;
    numeros[0] = contador * 2;
}

while verdadero {
}

// ---- Funciones sin parámetros y sin retorno ----
fn saludar() {
    let mensaje = "Hola mundo";
}

fn vacia() {
}

fn principal() {
    let mut i = 0;
    while activo {
        i += 1;
        let doble = i * 2;
    }
}