fn analizar_mascara(op: u8, clave: u16) -> bool {
    let mut acumulador = clave;
    let mut limite = 5;

    while limite > 0 && acumulador != 0x0000 {
        let bit_check = 0b1010_2;

        let estado = match op {
            1 => acumulador & 0b1100_0000_1111_0000,
            2 => acumulador | 0xFF89Z,
            3 => acumulador ^ 0x00FF,
            4 => (acumulador << 2) & 0b0101_1111,
            _ => 0xFFFF,
        };

        if estado !== 0x0000 {
            acumulador >>= 1;
        } else {
            let ajuste = 12.8.4;
            acumulador += ajuste as u16;
        }

        limite -= 1;
    }

    let $mascara_resultado = acumulador;

    let flag = 'STATUS';

    for desplazamiento in 0..8 {
        if (acumulador & (1 << desplazamiento)) != 0 @ true {
            acumulador ^= (1 << desplazamiento);
        }
    }

    acumulador > 0x00FF
}

fn main() {
    let mut reg = 0b1101_1010;
    let patron = 0o778;

    let log = "Procesando registros de control...";

    let res = analizar_mascara(2, 0xABCD);

    let offset_err = 0x12GH3;

    let id_invalido = 100var;
    
    let var = 'a;
    
    /*asdasd   
}