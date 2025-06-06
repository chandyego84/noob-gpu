#include <windows.h>
#include <stdio.h>

#define MAX_THREADS 8

int* data = NULL;
long long partial_sums[MAX_THREADS] = {0};

typedef struct {
    int start;
    int end;
    int thread_index;
} ThreadData;

DWORD WINAPI sum_part(LPVOID arg) {
    ThreadData* td = (ThreadData*)arg;
    long long sum = 0;
    for (int i = td->start; i < td->end; i++) {
        sum += data[i];
    }
    partial_sums[td->thread_index] = sum;
    return 0;
}

void run_test(int array_size, int num_cores) {
    data = (int*)malloc(array_size * sizeof(int));
    if (!data) {
        printf("Failed to allocate memory\n");
        return;
    }
    for (int i = 0; i < array_size; i++) {
        data[i] = 1;
    }

    HANDLE threads[MAX_THREADS];
    ThreadData thread_data[MAX_THREADS];
    int chunk_size = array_size / num_cores;

    LARGE_INTEGER frequency, start, end;
    QueryPerformanceFrequency(&frequency);

    // --- MULTITHREADED SUM ---
    QueryPerformanceCounter(&start);

    for (int i = 0; i < num_cores; i++) {
        thread_data[i].start = i * chunk_size;
        thread_data[i].end = (i == num_cores - 1) ? array_size : (i + 1) * chunk_size;
        thread_data[i].thread_index = i;

        threads[i] = CreateThread(NULL, 0, sum_part, &thread_data[i], 0, NULL);
        if (threads[i] == NULL) {
            printf("Error creating thread %d\n", i);
            free(data);
            return;
        }
    }

    WaitForMultipleObjects(num_cores, threads, TRUE, INFINITE);

    for (int i = 0; i < num_cores; i++) {
        CloseHandle(threads[i]);
    }

    long long total_sum = 0;
    for (int i = 0; i < num_cores; i++) {
        total_sum += partial_sums[i];
    }

    QueryPerformanceCounter(&end);
    double elapsed_multithread_ms = (double)(end.QuadPart - start.QuadPart) * 1000.0 / frequency.QuadPart;

    // --- SINGLE THREAD SUM ---
    QueryPerformanceCounter(&start);

    long long single_sum = 0;
    for (int i = 0; i < array_size; i++) {
        single_sum += data[i];
    }

    QueryPerformanceCounter(&end);
    double elapsed_single_ms = (double)(end.QuadPart - start.QuadPart) * 1000.0 / frequency.QuadPart;

    // Results
    printf("Array size: %d\n", array_size);
    printf("Multithreaded sum: %lld, time: %.3f ms\n", total_sum, elapsed_multithread_ms);
    printf("Single-threaded sum: %lld, time: %.3f ms\n", single_sum, elapsed_single_ms);
    printf("---------------------------------------------------\n");

    free(data);
}

int main() {
    SYSTEM_INFO sysinfo;
    GetSystemInfo(&sysinfo);
    int num_cores = sysinfo.dwNumberOfProcessors;
    if (num_cores > MAX_THREADS) num_cores = MAX_THREADS;

    // Test different sizes
    int sizes[] = {
        1000000,
        10000000,
        50000000,
        100000000,
        500000000,
        1000000000
    };
    int num_tests = sizeof(sizes) / sizeof(sizes[0]);

    for (int i = 0; i < num_tests; i++) {
        run_test(sizes[i], num_cores);
    }

    return 0;
}
