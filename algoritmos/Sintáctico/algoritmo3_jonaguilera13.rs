// Ejemplos con errores sintacticos intencionales.
let datos = (1, 2);
// ERROR 1: la tupla no tiene coma entre sus componentes.
let t = (1 2);
// ERROR 2: falta la expresion a la derecha de &&.
if datos.0 > 0 && { let a = 1; }
// ERROR 3: falta ':' entre parametro y tipo.
fn probar(x i32) { let a = 1; }
// ERROR 4: falta ':' en la definicion de un campo.
struct Persona { edad i32 }
// ERROR 5: falta '=>' en el brazo del match.
match datos.0 { 1 { let x = 1; }, _ => { let y = 2; } }
