// Errores sintácticos en variables, constantes, asignaciones y expresiones aritméticas.

let ok1 = 5;

// Error 1: falta el identificador
let = 5;
let ok2: i32 = 10;

// Error 2: falta el tipo después de ':'
let x: = 10;
let ok3 = ok1 + ok2;

// Error 3: la constante no tiene anotación de tipo
const LIMITE = 50;
let ok4 = 4;

// Error 4: falta la expresión después de '='
let y = ;
let ok5 = 5;

// Error 5: operador '*' sin operando izquierdo
let z = 4 + * 2;
let ok6 = 6;

// Error 6: paréntesis sin cerrar
let w = (3 + 4;
let ok7 = 7;

// Error 7: operador compuesto sin valor
ok1 += ;
let ok8 = 8;

// Error 8: falta el punto y coma
let ultimo = 7
