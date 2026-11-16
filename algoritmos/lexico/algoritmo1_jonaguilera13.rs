//Estos algoritmos permiten validar operadores relacionales, operadores lógicos, valores booleanos, palabras reservadas de estructuras de control y delimitadores de tuplas.
let edad = 21;
let limite = 65;
let activo: bool = true;
let suspendido: bool = false;

let mayor_edad = edad >= 18;
let menor_limite = edad <= limite;
let es_mayor = edad > 20;
let es_menor = edad < 30;
let es_igual = edad == 21;
let es_diferente = edad != 18;

let acceso = mayor_edad && activo;
let rechazo = suspendido || false;
let permitido = !suspendido;

let validacion = edad >= 18 && activo == true;
let restriccion = edad < 18 || suspendido != false;
let condicion = !(edad == 0);

let datos = (edad, activo, suspendido);
let coordenadas = (10, 20);
let estados = (true, false);