fn obtener_puerto() -> i32 {
    return 8080;
}

fn coordenadas_origen() -> (f64, f64) {
    return (0.0, 0.0);
}

fn calcular_descuento(precio: f64, es_vip: bool) -> f64 {
    if precio <= 0.0 {
        return 0.0;
    }

    if es_vip {
        return precio * 0.80;
    }

    return precio * 0.95;
}

fn generar_rango(inicio: i32, fin: i32) -> Vec<i32> {
    let mut lista: Vec<i32> = Vec::new();
    for i in inicio..=fin {
        lista.push(i);
    }
    return lista;
}

fn validar_limite(valor: i32) {
    if valor < 0 {
        return;
    }

    let mut contador = 0;
    while contador < valor {
        if contador == 10 {
            return;
        }
        contador += 1;
    }
}
use std::io;

fn main() {

    let puerto = obtener_puerto();
    let origen = coordenadas_origen();
    let total = calcular_descuento(150.0, true);
    let elementos = generar_rango(1, 5);

    validar_limite(puerto);
    validar_limite(-5);

    let suma_final = total + origen.0;
    let primer_elem = elementos[0];

    let mut suma = 0;

    for i in 0..5 {
        suma += i;
    }

    for n in 1..=10 {
        suma += n;
    }

    let inicio = 2;
    let limite = 8;
    for k in inicio..(limite * 2) {
        suma += k;
    }

    let numeros = vec![10, 20, 30, 40];
    for val in numeros {
        suma += val;
    }

    for item in [1, 2, 3] {
        suma += item;
    }

    for extra in vec![5, 10] {
        suma += extra;
    }

    let mut matriz = vec![vec![1, 2], vec![3, 4]];
    for fila in 0..2 {
        for col in 0..=1 {
            matriz[fila][col] += 1;
        }
    }


    let nombre = "Rust";
    let version = 2026;
    let precios = vec![10, 20, 30];

    println!();
    print!("Iniciando programa... ");
    println!("Listo.");
    println!("Lenguaje: {}, Año: {}", nombre, version);
    println!("Primer precio: {}, Suma: {}", precios[0], precios[1] + precios[2]);


    let mut nombre: String = String::new();
    let mut edad_texto = String::new();

    println!("Ingresa tu nombre:");

    io::stdin().read_line(&mut nombre);

    println!("Ingresa tu edad:");

    std::io::stdin().read_line(&mut edad_texto).unwrap();

    println!("Hola, {}! Edad registrada: {}", nombre, edad_texto);
}