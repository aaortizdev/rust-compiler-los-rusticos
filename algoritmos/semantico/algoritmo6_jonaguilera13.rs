//Todo está correcto.

const LIMITE: i32 = 10;

fn main() {
    let mut contador: i32 = 2;
    let media: f64 = 1.5 + 2.5;
    let habilitado: bool = true;
    let valido: bool = !false;
    let par: (i32, bool) = (3, true);
    let primero: i32 = par.0;

    contador += 1;
    if habilitado && valido && primero < LIMITE {
        contador = contador + 1;
    }
    while contador < LIMITE {
        contador += 1;
    }
    println!("{}", media);
}