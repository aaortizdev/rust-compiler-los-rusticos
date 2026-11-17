fn main() {
    // ERROR: una cadena no se puede asignar a un i32.
    let mensaje: i32 = "hola";

    let entero: i32 = 10;
    let decimal: f64 = 3.5;

    //ERROR: no se puede sumar i32 y f64.
    let suma = entero + decimal;

    // ERROR: no se puede sumar un número con bool.
    let mezcla = 5 + true;

    let mut contador: i32 = 4;

    // ERROR: la asignación simple cambia i32 por bool.
    contador = false;

    // ERROR: una asignación compuesta tampoco permite mezclar tipos.
    contador += 1.5;

    // ERROR: el tipo declarado es bool, pero el valor es entero.
    const ACTIVO: bool = 2;
}