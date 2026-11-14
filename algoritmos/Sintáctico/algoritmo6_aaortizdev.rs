// Errores sintácticos en arreglos, while y funciones.

let ok = 1;

// Error 1: falta ';' entre el tipo y el tamaño del arreglo
let a: [i32 3] = [1, 2, 3];
let ok2 = 2;

// Error 2: arreglo sin elemento final
let b = [1, 2, ];
let ok3 = 3;

// Error 3: acceso por índice sin expresión
let c = ok[];
let ok4 = 4;

// Error 4: while sin condición
while { ok = 1; }
let ok5 = 5;

// Error 5: while sin bloque
while ok
let ok6 = 6;

// Error 6: función con paréntesis sin cerrar
fn saludar( {
    let m = 1;
}
let ok7 = 7;

// Error 7: función sin cuerpo
fn sin_cuerpo();
let ok8 = 8;

// Error 8: falta el nombre de la función
fn () { }
let ok9 = 9;

// Error 9: bloque sin cerrar
fn incompleta() {
    let k = 1;