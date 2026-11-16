fn verificar(x: i32, activo: bool) {
    // ERROR: if necesita una condición bool.
    if 5 {
        println!("Condición incorrecta");
    }

    // ERROR: una suma de enteros no es una condición bool.
    while x + 1 {
        println!("Condición incorrecta");
    }

    // ERROR: el operando derecho es entero.
    if activo && 1 {
        println!("Operador incorrecto");
    }

    // ERROR: el operando izquierdo es entero.
    if x || activo {
        println!("Operador incorrecto");
    }

    // ERROR: ! no acepta un entero.
    if !x {
        println!("Negación incorrecta");
    }

    // CORRECTO: una comparación da bool y puede combinarse con &&.
    if x > 2 && activo {
        println!("Condición correcta");
    }
}
