// ------------------------------------------------------------
// Algoritmo de prueba semántico 3 - @aaortizdev (Ariel Ortiz)
// Programa: tabla de multiplicar y clasificación de números
// con for, match, funciones y ámbitos anidados.
// Prueba las reglas 1 (identificadores declarados) y
// 2 (mutabilidad y constantes).
// ------------------------------------------------------------
const TABLA: i32 = 7;

fn mostrar_tabla() {
    for i in 1..=10 {
        let producto = TABLA * i;
        println!("{} x {} = {}", TABLA, i, producto);
    }
    // ERROR regla 1: 'producto' solo existe dentro del for
    println!("Último producto: {}", producto);
}

fn clasificar(numero: i32) {
    let tipo = match numero {
        0 => 0,
        1 => 1,
        otro => otro * 2,
    };
    println!("Clasificación: {tipo}");

    // ERROR regla 1: 'otro' solo existe dentro de su brazo del match
    println!("{}", otro);
}

fn main() {
    let mut total = 0;
    let limite = 5;

    for j in 0..limite {
        total += j;
        // ERROR regla 2: 'j' es la variable del for
        j += 1;
    }

    // Shadowing correcto: se declara una nueva 'limite'
    let limite = limite * 2;
    println!("Total: {total}, nuevo límite: {limite}");

    if total > 3 {
        let mensaje = 1;
        total = total + mensaje;
    }
    // ERROR: 'mensaje' solo existe dentro del if
    total = total + mensaje;

    fn auxiliar() {
        // ERROR regla 1: 'total' es local de main
        println!("{}", total);
    }

    // ERROR: 'limite' (la nueva) también es inmutable
    limite = 20;
}