const MAX_INTENTOS: i32 = 100_000;

static FACTOR_ESCALA: f64 = 3.14_15;
static IP_HOME: f64 = 192.168.1.1;

fn main() {
    let mut contador: i32 = 0;
    let limite: u64 = 100;
    let factor: f32 = 3.14;

    let suma = 10 + 5;
    let resta = 10 - 5;
    let producto = 10 * 5;
    let cociente = 10 / 5;
    let residuo = 10 % 3;

    let mut contador_usuarios: u32 = 0;
    contador_usuarios += 1;
    contador_usuarios *= 2;
    contador_usuarios >>= 1;

    let caracter_raro = @;

    let arreglo_fijo: [i64; 3] = [10, 20, 30];
    let valor_grande: u128 = 1_000_000;
    let mut x: usize = 5;
    x += 5;
    x -= 3;
    x *= 2;
    x /= 4;
    x %= 4;
}