// ERROR 1 (Ingreso por teclado - importación): Falta el punto y coma ';' al final de 'use'
use std::io

pub struct Evaluacion {
    pub notas: Vec<f64>,
}

// ERROR 2 (Definición de métodos - impl): Falta el tipo de retorno después de '->'
impl Evaluacion {
    pub fn calcular_promedio(&self) -> {
        let mut suma = 0.0
        for n in self.notas {
            suma += n;
        }
        return suma;
    }
}

// Función válida de apoyo para probar llamadas
fn procesar_puntos(mut lista: Vec<i32> bono: i32) ->  {
    let mut total = 0;

    // ERROR 3 (Estructura de control - for): Falta la palabra clave 'in'
    for i 0..lista.len() {
        total += lista[i] + bono;
    }

    return total;


fn main() {
    // ERROR 4 (Vector - vec): Falta el cierre '>' en Vec<i32> y falta una coma entre 20 y 30
    let mut puntajes: Vec<i32 = vec![10, 20 30]
    puntajes.push(40)

    let mut entrada = String::new()
    println!("Ingrese el bono extra:");

    // ERROR 5 (Ingreso por teclado - lectura): Falta el '&' en '&mut entrada'
    io::stdin().read_line(mut entrada);

    // ERROR 6 (Llamada a función): Falta coma ',' entre los argumentos 'puntajes' y '5'
    let resultado = procesar_puntos(puntajes 5);

    // ERROR 7 (Impresión): Falta coma ',' después de la cadena de formato
    println!("El resultado final es: {}" resultado);
