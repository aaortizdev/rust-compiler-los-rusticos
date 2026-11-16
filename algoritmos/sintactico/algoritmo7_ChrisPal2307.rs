const LIMITE: i32 = 100;

pub struct Producto {
    pub id: i32,
    precio: f64,
}

impl Producto {
    pub fn limite_base() -> i32 {
        return LIMITE;
    }

    pub fn obtener_precio(&self) -> f64 {
        return self.precio;
    }

    pub fn actualizar_datos(&mut self, nuevo_id: i32, nuevo_precio: f64) {
        self.id = nuevo_id;
        self.precio = nuevo_precio;
    }
}

fn actualizar_catalogo(mut precios: Vec<f64>, mut prod: Producto) {
    precios.push(19.99);
    precios[0] += 5.50;

    prod.actualizar_datos(42, precios[0]);
    let actual = prod.obtener_precio();
    prod.precio = actual + 1.0;
}

fn main() {
    let tope = Producto::limite_base();

    let mut vacio: Vec<i32> = Vec::new();
    let mut con_espacio: Vec<bool> = Vec::with_capacity(5);
    let macro_vacio = vec![];
    let mut numeros = vec![10, 20, 30];
    let repetidos = vec![0; 4];

    vacio.push(1);
    vacio.push(2);
    vacio.pop();
    numeros.insert(1, 15);

    numeros[0] = 99;
    numeros[2] *= 2;
    let primero = numeros[0];

    let cantidad = numeros.len();
    let esta_vacio = vacio.is_empty();

    let mut pares: Vec<(i32, char)> = vec![(1, 'a'), (2, 'b')];
    pares[0].0 = 10;
    let letra = pares[1].1;

    let mut inventario: Vec<Producto> = Vec::new();
    let mut matriz: Vec<Vec<i32> > = vec![vec![1, 2], vec![3, 4]];
    let celda = matriz[0][1];

    let mut i = 0;
    while i < 3 && !esta_vacio {
        numeros.push(i * 10);
        i += 1;
    }

    if numeros[0] >= tope || cantidad == 3 {
        numeros[0] -= 10;
    } else if !(cantidad < 1) {
        numeros.push(0);
    } else {
        numeros.clear();
    }
}