// ------------------------------------------------------------
// Algoritmo de prueba semántico 1 - @aaortizdev (Ariel Ortiz)
// Programa: promedio de notas de un curso con arreglos y while.
// Prueba las reglas 1 (identificadores declarados) y
// 2 (mutabilidad y constantes).
// ------------------------------------------------------------
const NUM_ESTUDIANTES: usize = 5;
const NOTA_MINIMA: f64 = 6.0;

fn main() {
    let notas = [8.5, 4.0, 9.2, 5.5, 7.0];
    let mut aprobados = [0, 0, 0, 0, 0];
    let mut suma: f64 = 0.0;
    let mut indice = 0;
    let mut contador_aprobados = 0;

    while indice < NUM_ESTUDIANTES {
        suma += notas[indice];
        if notas[indice] >= NOTA_MINIMA {
            aprobados[indice] = 1;
            contador_aprobados += 1;
        }
        indice += 1;
    }

    let promedio = suma / 5.0;
    println!("Promedio del curso: {promedio}");
    println!("Aprobados: {}", contador_aprobados);

    // ERROR: 'notas' no fue declarada con 'mut'
    notas[1] = 6.5;

    // ERROR: no se puede reasignar una constante
    NOTA_MINIMA = 5.0;

    // ERROR: 'reprobados' nunca fue declarada
    println!("Reprobados: {}", reprobados);

    // ERROR: 'maximo' no existe (dentro del formato)
    println!("Nota más alta: {maximo}");

    // ERROR: 'promedio' es inmutable
    promedio = promedio + 0.5;
}