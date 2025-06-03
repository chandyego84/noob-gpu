    #include <stdio.h>
    #include <stdlib.h>

    #ifdef __APPLE__
    #include <OpenCL/opencl.h>
    #include <unistd.h>
    #else
    #include <CL/cl.h>
    #include "../err_code.h"
    #include "../device_info.h"
    #include <math.h>
    #include <time.h>
    #endif

    #define SIZE 1024
    #define TOL 1e-3 // tolerance level for testing correctness

    int main(void) {
        printf("-----------------------------\n");
        printf("MATMUL on a GPU\n");
        printf("-----------------------------\n");

        cl_int err;

        const char* kernel_source = "\n" \
        "__kernel void matmul( \n" \
            "const unsigned int M, \n" \
            "const unsigned int N, \n" \
            "const unsigned int K, \n" \
            "__global float* A, \n" \
            "__global float* B, \n" \
            "__global float* C \n" \
        ") \n" \
        "{ \n" \
            "const int global_row = get_global_id(0); // row ID of C \n" \
            "const int global_col = get_global_id(1); // col ID of C \n" \
            
            "// assuming memory in row-major order \n" \
            "// each element in C matrix has k fused multiply adds \n" \
            "float k_acc = 0.0f; \n" \
            "for (unsigned int k = 0; k < K; k++) { \n" \
                "k_acc += A[global_row * K + k] * B[N * k + global_col]; \n" \
            "} \n"\

            "// store result in C \n" \
            "C[global_row * N + global_col] = k_acc; \n" \
        "} \n";

        // DEFINE PLATFORM
        cl_int num_platforms;
        cl_platform_id platforms[num_platforms];
        cl_platform_id platform_id;
        cl_device_id device_id;
        cl_context context;
        cl_command_queue commands;

        err = clGetPlatformIDs(0, NULL, &num_platforms);
        checkError(err, "Finding number of platforms");
        
        // get plats
        err = clGetPlatformIDs(num_platforms, platforms, NULL);
        checkError(err, "Getting platforms");

        // get GPU device
        for (int plat_index = 0; plat_index < num_platforms; plat_index++) {
            err = clGetDeviceIDs(platforms[plat_index], CL_DEVICE_TYPE_GPU, 1, &device_id, NULL);
            if (err == CL_SUCCESS) {
                printf("Found a GPU device\n");
                output_device_info(device_id);
                break;
            }
        }

        if (err != CL_SUCCESS || device_id == NULL) {
            checkError(err, "Getting GPU Device");
        }

        // create context
        context = clCreateContext(0, 1, &device_id, NULL, NULL, &err);
        checkError(err, "Creating context");

        // create command queue for device
        commands = clCreateCommandQueueWithProperties(context, device_id, 0, &err);
        checkError(err, "Creating command queue for device");

        // BUILD PROGRAM
        cl_program program;
        program = clCreateProgramWithSource(context, 1, (const char**) &kernel_source, NULL, &err);
        checkError(err, "Creating program");

        // compile program
        err = clBuildProgram(program, 1, &device_id, NULL, NULL, NULL);

        printf("Built and compiled program\n");
        
        // SET UP MEMORY
        unsigned int count = SIZE * SIZE;
        float* h_a = (float*)malloc(sizeof(float) * count);
        float* h_b = (float*)malloc(sizeof(float) * count);
        float* h_c = (float*)malloc(sizeof(float) * count);
        for (int i = 0; i < count; i++) {
            h_a[i] = rand() / (float)RAND_MAX;
            h_b[i] = rand() / (float)RAND_MAX;
        }
        printf("Assigned values to input matrices on host\n");

        cl_mem d_a;
        cl_mem d_b;
        cl_mem d_c;

        // create buffers on device
        d_a = clCreateBuffer(context, CL_MEM_READ_ONLY, sizeof(float) * count, NULL, &err);
        d_b = clCreateBuffer(context, CL_MEM_READ_ONLY, sizeof(float) * count, NULL, &err);
        d_c = clCreateBuffer(context, CL_MEM_WRITE_ONLY, sizeof(float) * count, NULL, &err);

        // write input matrices to device memory
        err = clEnqueueWriteBuffer(commands, d_a, CL_BLOCKING, 0, sizeof(float) * count, h_a, 0, NULL, NULL);
        checkError(err, "Writing into d_a from h_a");
        
        err = clEnqueueWriteBuffer(commands, d_b, CL_BLOCKING, 0, sizeof(float) * count, h_b, 0, NULL, NULL);
        checkError(err, "Writing into d_b from h_b");
        
        printf("Wrote input matrices into device memory\n");

        // KERNEL EXECUTE
        // create kernel obj
        cl_kernel mat_mul_ko;
        const char* kernel_name = "matmul";
        mat_mul_ko = clCreateKernel(program, kernel_name, &err);
        printf("Created kernel obj\n");

        // set kernel args
        // M, N, K, A matrix, B matrix, C output matrix
        const unsigned int count_per_dim = SIZE;
        err = clSetKernelArg(mat_mul_ko, 0, sizeof(const unsigned int), &count_per_dim);
        err |= clSetKernelArg(mat_mul_ko, 1, sizeof(const unsigned int), &count_per_dim);
        err |= clSetKernelArg(mat_mul_ko, 2, sizeof(const unsigned int), &count_per_dim);
        err |= clSetKernelArg(mat_mul_ko, 3, sizeof(d_a), &d_a);
        err |= clSetKernelArg(mat_mul_ko, 4, sizeof(d_b), &d_b);
        err |= clSetKernelArg(mat_mul_ko, 5, sizeof(d_c), &d_c);
        checkError(err, "Creating kernel args");

        printf("Set kernel args\n");

        // enqueue 2d kernel
        srand(time(NULL));
        clock_t start, end;
        const size_t global_size[2]= {SIZE, SIZE};

        float flop = (float) SIZE * SIZE * 2 * SIZE;
        printf("%.6f GFLOP to multiply matrices\n", flop/1e9);

        err = clEnqueueNDRangeKernel(commands, mat_mul_ko, 2, NULL, global_size, NULL, 0, NULL, NULL);
        checkError(err, "Setting up 2d kernel");

        start = clock();
        err = clFinish(commands);
        end = clock();

        double gpu_time = ((double) (end - start)) / CLOCKS_PER_SEC;
        checkError(err, "Finishing commands in device");

        printf("GPUP Time: %f seconds\n", gpu_time);
        printf("%.6f TFLOP/S\n", flop/gpu_time/1e12);

        // read back result from device to host
        err = clEnqueueReadBuffer(commands, d_c, CL_TRUE, 0, sizeof(float) * count, h_c, 0, NULL, NULL);
        checkError(err, "Reading results back from device to host");

        // Test Results
        int correct = 0;
        // SIZE = M = N = K
        for (int i = 0; i < SIZE; i++) {
            for (int j = 0; j < SIZE; j++) {
                float expected = 0.0f;
                for (int k = 0; k < SIZE; k++) {
                    expected += h_a[SIZE * i + k] * h_b[SIZE * k + j]; // h_a[K * i + k] * h_b[K * k + j]  
                }

                float actual = h_c[SIZE * i + j]; // h_c[N * i + j]
                float diff = fabs(actual - expected);
                if (diff * diff < TOL * TOL) {
                    correct++;
                }
            }
        }

        printf("%d correct / %d total\n", correct, count);

        free(h_a);
        free(h_b);
        free(h_c);
    }