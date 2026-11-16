use std::thread;
use std::sync::Arc;

fn multiplicar_matrices_hilos(mat_a: Vec<Vec<i32>>, mat_b: Vec<Vec<i32>>) -> Vec<Vec<i32>> {
    let filas_a = mat_a.len();
    let columnas_a = mat_a[0].len();
    let filas_b = mat_b.len();
    let columnas_b = mat_b[0].len();

    assert_eq!(columnas_a, filas_b, "Las columnas de A deben coincidir con las filas de B");

    let mat_a_arc = Arc::new(mat_a);
    let mat_b_arc = Arc::new(mat_b);

    let mut handles = Vec::new();

    for i in 0..filas_a {
        let mat_a_ref = Arc::clone(&mat_a_arc);
        let mat_b_ref = Arc::clone(&mat_b_arc);

        let handle = thread::spawn(move || {
            let mut fila_resultado = vec![0; columnas_b];

            for j in 0..columnas_b {
                let mut suma = 0;
                for k in 0..columnas_a {
                    suma += mat_a_ref[i][k] * mat_b_ref[k][j];
                }
                fila_resultado[j] = suma;
            }

            fila_resultado
        });

        handles.push(handle);
    }

    let mut resultado = Vec::with_capacity(filas_a);

    for handle in handles {
        let fila = handle.join().unwrap();
        resultado.push(fila);
    }

    resultado
}

fn main() {
    let matriz_a = vec![
        vec![1, 2, 3],
        vec![4, 5, 6],
        vec![7, 8, 9],
    ];

    let matriz_b = vec![
        vec![9, 8, 7],
        vec![6, 5, 4],
        vec![3, 2, 1],
    ];

    let matriz_c = multiplicar_matrices_hilos(matriz_a, matriz_b);

    println!("Resultado de la multiplicacion matricial:");
    for fila in matriz_c {
        println!("{:?}", fila);
    }
}