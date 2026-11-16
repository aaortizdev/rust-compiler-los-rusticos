// ------------------------------------------------------------
// Algoritmo de prueba semántico 2 - @aaortizdev (Ariel Ortiz)
// Programa: cuenta bancaria con struct, impl, lectura de datos
// y vector de movimientos.
// Prueba las reglas 1 (identificadores declarados) y
// 2 (mutabilidad y constantes).
// ------------------------------------------------------------
use std::io;

const SALDO_MAXIMO: f64 = 10000.0;

struct Cuenta {
    titular: String,
    saldo: f64,
}

impl Cuenta {
    fn consultar(&self) -> f64 {
        return self.saldo;
    }

    fn depositar(&mut self, monto: f64) {
        self.saldo += monto;
    }

    // ERROR: recibe '&self', no puede modificar 'self'
    fn retirar(&self, monto: f64) {
        self.saldo -= monto;
    }

    // ERROR: el parámetro 'monto' no es 'mut'
    fn aplicar_comision(&mut self, monto: f64) {
        monto = monto * 0.02;
        self.saldo -= monto;
    }
}

fn main() {
    let mut entrada = String::new();
    let mut movimientos = Vec::new();
    let historial = Vec::new();

    println!("Ingrese el monto a depositar:");
    io::stdin().read_line(&mut entrada).expect("Error al leer");

    movimientos.push(100.0);
    movimientos.push(250.0);

    // ERROR: 'historial' es inmutable y push lo modifica
    historial.push(50.0);

    let confirmacion = String::new();
    // ERROR: '&mut' de una variable inmutable
    io::stdin().read_line(&mut confirmacion).expect("Error al leer");

    // ERROR: 'cuenta' nunca fue declarada
    println!("Saldo: {}", cuenta);

    // ERROR: constante
    SALDO_MAXIMO -= 500.0;
}