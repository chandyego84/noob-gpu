/**
 * ------------------------------
 * BASIC TERMS
 * ------------------------------
 * Kernel execution commands - Execute a kernel on the processing elements of a device
 * Memory commands - Transfer data to/from/between memory objects, or map/unmap memory objects from the host address space
 * Synchronization commands - Constrain the order of execution of commands
 * ------------------------------
 * ------------------------------
 * IDs
 * ------------------------------
 * An index space is defined when a kernel is submitted for execution by the host
    * Kernel instance = work-item -- identified by its point in index space
        * index space provides global ID for work-item
    * Work-items are organized into work-groups
        * Work-groups are assigned work-group ID (same dimensions as index space above)
        * Work-items assigned local ID within work-group (can be identified by global ID or local ID + work-group ID)
 * NDRange
    * N-dimensional index space, where N = 1, 2, or 3
    * integer array of length N, specifying the extent of the index space in each dimension
        * starting @ an offset index F (zero default)
    * each work-item's global ID and local ID are N-dimensional tuples
    * Work-groups assigned IDs using array of length N which defines # of work-groups in each dimension
 * ------------------------------
 * DIMENSIONS
 * ------------------------------
 * Global dimensions - the whole problem space (e.g., 1024x1024 image space)
 * Local dimensions - work-group/thread block that executes together (e.g., 64x64 section of the image space)
 * ------------------------------
 * MEMORY
 * ------------------------------
 * Private memory - per thread
 * Local memory - per work-group
 * Global memory - visible to all work-groups (work-group grid)
 * Host memory - on the CPU
 * You are responsibled for managing data between host, global, local and back
 * ------------------------------
 * CONTEXT & COMMAND QUEUES
 * ------------------------------
 * Context - environment within which kernels execute and synchronization/memory management is defined
    * includes one or more devices, device memory, one or more command queues
 * Command - commands for a device are submitted through a command queue
    * Each command-queue points to a single device within a context
 * ------------------------------
 * BASIC STEPS FOR A NOOB HOST PROGRAM
 * ------------------------------
 * Host program - code that runs on the host to manage kernels and environment for the OpenCL program
 * 1. Define the platform (devices, context, queues)
 * 2. Create and build the program (dynamic library for kernels)
 * 3. Setup memory objects
 * 4. Define the kernel (attach args to kernel functions)
 * 5. Submit commands (transfer memory objects and execute kernels)
 */

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

int main(void)
{
    cl_int err;

    // kernel code
    const char* kernel_code = "\n" \
    "__kernel void vector_add( \n" \
    "   __global float* a,\n" \
    "   __global float* b,\n" \
    "   __global float* c,\n" \
    "   const unsigned int count) \n" \
    "{ \n" \
    "   int i = get_global_id(0); \n" \
    "   if (i < count) { \n" \
    "       c[i] = a[i] + b[i]; \n" \
    "   } \n" \
    "} \n"; 

    /**
     * DEFINE THE PLATFORM
     */
    // get number of platforms available
    cl_int num_platforms;

    err = clGetPlatformIDs(0, NULL, &num_platforms);
    checkError(err, "Finding number of platforms");
    if (num_platforms == 0) {
        printf("No platforms found\n");
    }
    else printf("Found %d platforms\n", num_platforms);

    // get all platforms
    cl_platform_id platforms[num_platforms];
    err = clGetPlatformIDs(num_platforms, platforms, NULL);
    checkError(err,"Getting all platforms"); 

    // get GPU device
    cl_device_id device_id;
    for (int i = 0; i < num_platforms; i++) {
        err = clGetDeviceIDs(platforms[i], CL_DEVICE_TYPE_GPU, 1, &device_id, NULL);
        if (err == CL_SUCCESS) {
            printf("Found a GPU device: ");
            output_device_info(device_id);
            break;
        }
    }
    
    if (device_id == NULL) checkError(err, "Finding device");

    // create context for device
    cl_context context;
    cl_platform_id first_platform_id = platforms[0];
    context = clCreateContext(0, 1, &device_id, NULL, NULL, &err);
    checkError(err, "Creating context for device");
    printf("Created context for device.\n");

    // create command-queue to feed device
    cl_command_queue commands = clCreateCommandQueueWithProperties(context, device_id, 0, &err);
    checkError(err,"Creating command queue for device");
    printf("Built command queue for device.\n");

    /**
     * BUILD THE PROGRAM
     */
    // build program object
    cl_program program;
    program = clCreateProgramWithSource(context, 1, (const char**) &kernel_code, NULL, &err);
    checkError(err, "Building the program project.");

    // compile the program
    err = clBuildProgram(program, 0, NULL, NULL, NULL, NULL);
    if (err != CL_SUCCESS) {
        size_t len;
        char buffer[2048];
        clGetProgramBuildInfo(program, device_id, CL_PROGRAM_BUILD_LOG, sizeof(buffer), buffer, &len);
        printf("%s\n", buffer);
    }

    /**
     * SET UP MEMORY OBJECTS
     */
    // for vector addition, we need 3 memory objects (one for each input vector and one for output vector)
    // create input vectors and assign values on the host
    float h_a[LENGTH], h_b[LENGTH], h_c[LENGTH];
    unsigned int count = LENGTH;
    for (int i = 0; i < LENGTH; i++) {
        h_a[i] = rand() / (float)RAND_MAX;
        h_b[i] = rand() / (float)RAND_MAX;
    }
        
    // MEMORY OBJECTS - handle to a reference-counted region of global memory

        // Buffer objects - 1D collection of elements (linear collection of bytes)
            // The contents of buffer objects are fully exposed within kernels and can be accessed using pointers
            // Elements of a bufffer object can be scalar (int, float), vector, or user-defined structure
        
        // Image objects - defines a 2 or 3-D region of memory
            // Can ONLY be accessed with read and write functions 

    cl_mem d_a = clCreateBuffer(context, CL_MEM_READ_ONLY, sizeof(float) * count, NULL, &err);
    checkError(err, "Creating buffer for d_a");

    cl_mem d_b = clCreateBuffer(context, CL_MEM_READ_ONLY, sizeof(float) * count, NULL, &err);
    checkError(err, "Creating buffer for d_b");

    cl_mem d_c = clCreateBuffer(context, CL_MEM_WRITE_ONLY, sizeof(float) * count, NULL, &err);
    checkError(err, "Creating buffer for d_c");

    if (err == CL_SUCCESS) printf("Created buffers for vectors\n");

    // Write a, b vectors into device memory
    err = clEnqueueWriteBuffer(commands, d_a, CL_TRUE, 0, sizeof(float) * count, h_a, 0, NULL, NULL);
    checkError(err, "Writing v_a buffer into device memory");

    err = clEnqueueWriteBuffer(commands, d_b, CL_TRUE, 0, sizeof(float) * count, h_b, 0, NULL, NULL);
    checkError(err, "Writing v_b buffer into device memory");

    if (err == CL_SUCCESS) printf("Wrote v_a and v_b to device\n");

    /**
     * KERNEL EXECUTION
     */
    cl_kernel vector_add_ko = clCreateKernel(program, "vector_add", &err);
    checkError(err, "Creating kernel object");
    
    if (err == CL_SUCCESS) printf("Created kernel object\n");

    // set kernel args
    err = clSetKernelArg(vector_add_ko, 0, sizeof(cl_mem), &d_a);
    err |= clSetKernelArg(vector_add_ko, 1, sizeof(cl_mem), &d_b);
    err |= clSetKernelArg(vector_add_ko, 2, sizeof(cl_mem), &d_c);
    err |= clSetKernelArg(vector_add_ko, 3, sizeof(unsigned int), &count);

    // enqueueing 1D kernel where local size (work group size is set by OpenCL)
    size_t global = count;
    // size_t local = 256;
    err = clEnqueueNDRangeKernel(commands, vector_add_ko, 1, NULL, &global, NULL, 0, NULL, NULL);
    checkError(err, "Enqueueing the kernel");

    if (err == CL_SUCCESS) printf("Enqueued kernel\n");

    err = clFinish(commands);
    checkError(err, "Waiting for kernel to finish");

    // read back the result from the device -- have an in-order queue, so CL_TRUE to assure previous commands are completed before read can begin
    err = clEnqueueReadBuffer(commands, d_c, CL_TRUE, 0, sizeof(float) * count, h_c, 0, NULL, NULL);
    checkError(err, "Reading back result from device");

    // Testing results
    int correct = 0;
    for (int i = 0; i < count; i++) {
        float expected = h_a[i] + h_b[i];
        float actual = h_c[i];
        if (expected == actual) {
            correct++;
        }
        // printf("Expected: %f, Actual: %f\n", expected, actual);
    }

    printf("V_ADD Results: %d correct / %d total", correct, count);

    // Clean up
    clReleaseMemObject(d_a);
    clReleaseMemObject(d_b);
    clReleaseMemObject(d_c);
    clReleaseProgram(program);
    clReleaseKernel(vector_add_ko);
    clReleaseCommandQueue(commands);
    clReleaseContext(context);
}