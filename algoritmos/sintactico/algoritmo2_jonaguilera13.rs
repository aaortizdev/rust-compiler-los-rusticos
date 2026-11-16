// estructuras, campos, match y funciones.
struct Persona {
    pub edad: i32,
    nombre: &str,
    activa: bool,
}

struct Medicion {
    pub datos: (i32, bool),
    valor: f64,
}

struct Vacia {}

fn procesar(nombre: &str, datos: (i32, bool), mut veces: i32) {
    let edad = datos.0;
    let activo = datos.1;
    while veces > 0 && activo {
        veces -= 1;
    }

    match edad {
        0 => { let categoria = "cero"; }
        18 => { let categoria = "adulto"; }
        _ => { let categoria = "otro"; }
    }
}

let persona_edad = 18;
let estado = (persona_edad, true);
procesar("Ana", estado, 2);

let categoria = match persona_edad {
    0 => 1,
    18 => 2,
    _ => 3,
};

match estado.1 {
    true => { let mensaje = "Activo"; },
    false => { let mensaje = "Inactivo"; },
}