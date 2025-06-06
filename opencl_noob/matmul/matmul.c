#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <omp.h>

// allocate matrix dynamically
float** allocate_matrix(unsigned int rows, unsigned int cols) {
    // allocate rows
    float** matrix = malloc(rows * sizeof(float*));
    if (matrix != NULL) {
        for (int i = 0; i < rows; i++) {
            // allocate space for cols in each row
            matrix[i] = malloc(cols * sizeof(float));
        }    
    }

    return matrix;
}

// free a matrix
void free_matrix(float** matrix, unsigned int rows) {
    for (int i = 0; i < rows; i++) {
        // free each row
        free(matrix[i]);
    }

    free(matrix);
}

// Multiply two matrices: A(m x p) * (p x n)
void matrix_multiply(float** mat_A, float** mat_B, float** mat_C, unsigned int m, unsigned int n, unsigned int p) {
    #pragma omp parallel
    {
        for (int i = 0; i < m; i++) {
            for (int j = 0; j < n; j++) {
                float sum = 0.0f;
                for (int k = 0; k < p; k++) {
                    sum += mat_A[i][k] * mat_B[k][j];
                }
                mat_C[i][j] = sum;
            }
        }
    }
}

void print_matrix(float** matrix, int rows, int cols, const char* name) {
    printf("%s = [\n", name);
    for (int i = 0; i < rows; i++) {
        printf("  ");
        for (int j = 0; j < cols; j++) {
            printf("%10.6f ", matrix[i][j]);
        }
        printf("\n");
    }
    printf("]\n\n");
}


int main(void) {
    srand(time(NULL));
    clock_t start, end;
    unsigned int m = 1024, n = 1024, k = 1024;

    // allocate matrices
    float** mat_A = allocate_matrix(m, k);
    float** mat_B = allocate_matrix(k, n); 
    float** mat_C = allocate_matrix(m, n);

    // set matrices values to random numbers
    for (int i = 0; i < m; i++) {
        for (int j = 0; j < k; j++) {
            mat_A[i][j] = rand() / (float)RAND_MAX;
        }
    }

    for (int i = 0; i < k; i++) {
        for (int j = 0; j < n; j++) {
            mat_B[i][j] = rand() / (float)RAND_MAX;
        }
    }

    // print_matrix(mat_A, m, k, "Matrix A");
    // print_matrix(mat_B, k, n, "Matrix B");

    // Compute for multiplying matrices
        // Output matrix is m x n (here, m = n). Each element in output matrix is a dot product of K-element vectors
        // A total of m*n*k fused multiply-adds occurs (eacyh FMA has two ops: add, mult) so FLOPS = m * n * 2k
    // Perf of a function on a processor is limited by one of three factors: memory, bandwidth, latency 
    // Arithmetic intensity: FLOPs:bytes accessed (read/written from memory) ratio
        // used to estimate if a particular matmul is math or memory limited
        // compare its arith intensity to the ops:byte ratio of the GPU
        // matmul < GPU AI ? memory limited : math limited (compute limited)
    float flop = (float)m * n * 2 * k; 
    printf("%.4f GFLOP to multiply matrices\n", flop / 1e9);

    start = clock();
    matrix_multiply(mat_A, mat_B, mat_C, m, n, k);
    end = clock();

    double cpu_time = ((double) (end - start)) / CLOCKS_PER_SEC;
    printf("CPU Time: %f seconds\n", cpu_time);
    printf("%.6f TFLOP/S\n", flop / cpu_time / 1e12);

    // print_matrix(mat_C, m, n, "Matrix C");

    // free memory
    free_matrix(mat_A, m);
    free_matrix(mat_B, k);
    free_matrix(mat_C, m);
}