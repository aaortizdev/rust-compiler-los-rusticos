//Estos algoritmos permiten validar operadores relacionales, operadores lógicos, valores booleanos, palabras reservadas de estructuras de control y delimitadores de tuplas.
let activo: bool = true;
let suspendido: bool = false;
let edad = 21;

let prueba1 = edad >= 18;
let prueba2 = activo == true;
let prueba3 = edad != 20;

let error1 = true &&& false;
let error2 = false ||| true;
let error3 = true & false;
let error4 = false | true;

let correcto1 = activo && !suspendido;
let correcto2 = edad <= 30 || edad > 18;

let datos = (edad, activo);
let valores = (true, false);

if activo == true
else
while edad < 30
match suspendido
true => break
false => continue
