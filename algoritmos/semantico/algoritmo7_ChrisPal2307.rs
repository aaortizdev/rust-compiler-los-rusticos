fn main() {
    println!("{}", retorno_implicito(5));
    println!("{}", retorno_explicito(-3));
    println!("{}", retorno_mixto(10));

    sin_retorno();
    sin_retorno_vacio(true);
    retorno_unidad();
}

// --- VÁLIDOS ---

fn retorno_implicito(x: i32) -> i32 {
    x * 2
}

fn retorno_explicito(x: i32) -> i32 {
    if x < 0 {
        return 0;
    }
    return x;
}

fn sin_retorno() {
    let _a = 10;
}

fn sin_retorno_vacio(salir: bool) {
    if salir {
        return;
    }
    println!("Continúa");
}

fn retorno_unidad() -> () {
    return ();
}

// --- ERRORES ---


fn err_return_tipo() -> i32 {
    return "texto";
}

fn err_implicito_tipo() -> i32 {
    "texto"
}

fn err_sin_retorno_explicito() {
    return 100;
}

fn err_sin_retorno_implicito() {
    "hola"
}

