// Tuplas, relaciones, logica y if / else.
let mut datos: (i32, bool, i32) = (20, true, 7);
let edad = datos.0;
let activo = datos.1;
let puntaje = datos.2;
let primer_dato: (i32,) = (5,);
let vacia: () = ();

datos.2 = 10;
let permitido = edad >= 18 && activo == true && !(puntaje < 0);
let alternativa = edad != 0 || (puntaje > 5 && edad <= 65);

if permitido && alternativa {
    let mensaje = "Acceso permitido";
} else if edad < 18 || !activo {
    let mensaje = "Acceso denegado";
} else {
    let mensaje = "Pendiente";
}

fn evaluar(edad: i32, activo: bool) {
    let valido = edad >= 18 && activo;
    if valido {
        let resultado = 1;
    } else {
        let resultado = 0;
    }
}

evaluar(edad, activo);
