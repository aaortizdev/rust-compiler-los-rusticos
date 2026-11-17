fn main() {
    let resultado: i32 = calcular_doble_suma(5, 10);
    
    imprimir_estado(es_mayor(resultado, 20));
    
    proceso_vacio();
}

fn calcular_doble_suma(x: i32, y: i32) -> i32 {
    let base = sumar(x, y);
    base * 2
}

fn sumar(a: i32, b: i32) -> i32 {
    return a + b;
}

fn es_mayor(valor: i32, limite: i32) -> bool {
    if valor > limite {
        return true;
    }
    false
}

fn proceso_vacio() {
    let activo = true;
    if activo {
        return;
    }
}

fn imprimir_estado(ok: bool) {
    let estado = ok;
}