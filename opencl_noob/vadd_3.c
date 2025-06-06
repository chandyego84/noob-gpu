#include <stdio.h>
#include <stdlib.h>

#ifdef __APPLE__
#include <OpenCL/opencl.h>
#include <unistd.h>
#else
#include <CL/cl.h>
#include "err_code.h"
#include "device_info.h"
#endif

#define LENGTH 1024

int main(void) {
    cl_int err;

    const char* kernel_source = "\n" \
    "__kernel void vadd_3( \n" \
    "   __global float* a,\n" \
    "   __global float* b,\n" \
    "   __global float* c,\n" \
    "   __global float* d, \n" \
    "   const unsigned int count) \n" \
    "{ \n" \
    "   int i = get_global_id(0); \n" \
    "   if (i < count) { \n" \
    "       d[i] = a[i] + b[i] + c[i]; \n" \
    "   } \n" \
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
    printf("Found %d platforms.\n", num_platforms);
    
    // get platforms
    err = clGetPlatformIDs(num_platforms, platforms, NULL);
    checkError(err, "Getting platforms");

    // get GPU device
    for (int p_id = 0; p_id < num_platforms; p_id++) {
        err = clGetDeviceIDs(platforms[p_id], CL_DEVICE_TYPE_GPU, 1, &device_id, NULL);
        if (err == CL_SUCCESS) {
            printf("Found a GPU Device\n");
            break;
        }
    }

    if (device_id == NULL) {
        checkError(err, "Getting GPU device\n");
    }

    // create context
    context = clCreateContext(0, 1, &device_id, NULL, NULL, &err);
    checkError(err, "Creating context\n");

    // create command-queue for device
    commands = clCreateCommandQueueWithProperties(context, device_id, 0, &err);
    checkError(err, "Creating command queue for device\n");

    // BUILD PROGRAM
    cl_program program;
    program = clCreateProgramWithSource(context, 1, (const char**) &kernel_source, NULL, &err);
    checkError(err, "Creating program");

    // compile program
    err = clBuildProgram(program, 1, &device_id, NULL, NULL, NULL);

    // SET UP MEMORY
    float h_a[LENGTH], h_b[LENGTH], h_c[LENGTH], h_d[LENGTH]; // buffers on host
    unsigned int count = LENGTH;
    for (int i = 0; i < LENGTH; i++) {
        h_a[i] = rand() / (float)RAND_MAX;
        h_b[i] = rand() / (float)RAND_MAX;
        h_c[i] = rand() / (float)RAND_MAX;
    }

    cl_mem d_a;
    cl_mem d_b;
    cl_mem d_c;
    cl_mem d_d;
    cl_kernel vector_add3_ko;


    // create buffers for device
    d_a = clCreateBuffer(context, CL_MEM_READ_ONLY, sizeof(float) * count, NULL, &err);

    d_b = clCreateBuffer(context, CL_MEM_READ_ONLY, sizeof(float) * count, NULL, &err);

    d_c = clCreateBuffer(context, CL_MEM_READ_ONLY, sizeof(float) * count, NULL, &err);

    d_d = clCreateBuffer(context, CL_MEM_WRITE_ONLY, sizeof(float) * count, NULL, &err);

    // write input vectors to device memory
    err = clEnqueueWriteBuffer(commands, d_a, CL_BLOCKING, 0, sizeof(h_a), h_a, 0, NULL, NULL);
    checkError(err, "Writing d_a buffer to h_a");

    err = clEnqueueWriteBuffer(commands, d_b, CL_BLOCKING, 0, sizeof(h_b), h_b, 0, NULL, NULL);
    checkError(err, "Writing d_b buffer to h_b");

    err = clEnqueueWriteBuffer(commands, d_c, CL_BLOCKING, 0, sizeof(h_c), h_c, 0, NULL, NULL);
    checkError(err, "Writing d_c buffer to h_c");

    // KERNEL EXECUTE
    // create kernel object
    const char* kernel_name = "vadd_3";
    vector_add3_ko = clCreateKernel(program, kernel_name, &err);
    checkError(err, "Creating kernel object");

    // set kernel args
    err = clSetKernelArg(vector_add3_ko, 0, sizeof(d_a), &d_a);
    err |= clSetKernelArg(vector_add3_ko, 1, sizeof(d_b), &d_b);
    err |= clSetKernelArg(vector_add3_ko, 2, sizeof(d_c), &d_c);
    err |= clSetKernelArg(vector_add3_ko, 3, sizeof(d_d), &d_d);
    err |= clSetKernelArg(vector_add3_ko, 4, sizeof(count), &count);
    checkError(err, "Setting kernel args"); 

    // enqueue 1d kernel
    size_t global_size = count;
    err = clEnqueueNDRangeKernel(commands, vector_add3_ko, 1, NULL, &global_size, NULL, 0, NULL, NULL);
    checkError(err, "Setting up 1d kernel");

    err = clFinish(commands);
    checkError(err, "Finishing commands in device");

    // read back result from the device
    err = clEnqueueReadBuffer(commands, d_d, CL_TRUE, 0, sizeof(float) * count, h_d, 0, NULL, NULL);
    checkError(err, "Reading results back from device");

    // TEST RESULTS
    unsigned int correct = 0;
    for (int t = 0; t < count; t++) {
        float expected = h_a[t] + h_b[t] + h_c[t];
        float actual = h_d[t];
        printf("Expected: %f: Actual: %f\n", expected, actual);
        if (expected == actual) {
            correct++;
        }
    }

    printf("%d correct\n", correct);

    if (correct == count) {
        printf("%d correct / %d total", correct, count);
    }
}