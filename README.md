# Noob GPU
## What do GPUs do?  
- GPUs process multiple data streams simultaneously
- They have lower clock speeds than CPUs
- They have higher memory bandwidth than CPUs (optimized for througput)

## Common Terminology and Basic Information
### SIMD/SIMT Paradigm:  
- __SIMT__ - Threads are explicitly defined by programmer; you can see thread ID and are aware of the thread as a unit of execution. 
- __SIMD__ - Lanes are implicit. They are built into GPU hardware and process threads simultaneously.  
GPUs expose the SIMT programmihng model while execution is implemented in GPU compute units/streaming multiprocessors. 

### NVIDIA/AMD Terminology:  
- Kernel - think C functions. Unit of a code program that is called once and returned once but executed many times over multiple threads.
- Thread/Work-item - simplest unit of execution. A sequence of instructions. Think of vector additon C[i] = A[i] + B[i]; each addition can be seen as a thread. For example:  
    - Load A[i] into Vector0 for all lanes
    - Load B[i] into Vector1 for all lanes
    - Add Vector0 and Vector1 and store into Vector2 for all lanes
    - Store Vector2 into memory (C[i]) for all lanes
    
- Thread block/Work-group - smallest unit of thread coordination exposed to programmers.
    - Composed of several threads
    - Each block is assigned to a SM/CU, and a SM/CU can accomodate several blocks
    - Arbitrarily sized (typically multiples of the warp size)

- Warp/Wavefront - Group of threads scheduled together and execute in parallel--these threads have the same operations that need to be executed
    - Each thread block is composed of warps/wavefronts which can be executed in lockstep
    - All threads in a warp are scheduled onto a sigle SM/CU--a single SM/CU can typically store and execute multiple warps/wavefronts
    - The results of the execution may of a warp/wavefront usually do not occur in a single clock cycle
    - For AMD GPUs: wavefront size is 64 threads 

- Streaming Multiprocessor (SM)/Compute Unit (CU) -The processing heart of GPUs
    - Contains warp/wavefront scheduler and SIMD units (plus others like cache, scalar units, local data share, etc., but those are not important for the purposes of this) 

### Example Pipeline
1. Kernel Launch  
    - Host (CPU) launches the kernel with a grid of thread blocks/work groups. Each block contains many threads/work items.  
    - GPU scheduler sends these blocks to the SMs/CUs.  

2. A wavefront is dispatched/issued to each SIMD unit inside the SM/CU using a scheduling algorithm (like Round-Robin) 
    - Within a block, threads are grouped into wavefronts (AMD GCN1 - 64 threads).  
    - All wavefronts in a block are guaranteed to reside in the same CU.
    - The SM's/CU's scheduler can hold wavefronts from many blocks (GCN1 - 40 wavefronts/CU, up to 10 wavefronts/SIMD unit). The specific amount of wavefronts that can be held by a SIMD unit depend on its resource availability (occupancy).
    - If a wavefront on a SIMD unit stalls (e.g., waiting for memory), the SIMD can switch to another ready wavefront from its buffer, keeping the hardware busy -- aka 'hiding memory latency'.
    - __At each clock cycle__: 
        - The warp scheduler issues a warp/wavefront to one of the SIMD units. 
        - At most 1 instruction per wavefront may be issued.

3. Each SIMD unit executes the same instruction for all the threads in a wavefront in lockstep

4. Repeat until all wavefronts exhausted/done executing in SM/CU

## NOOB GPU Architecture
### GPU
![GPU_TOP](img/NOOB_GPU_TOP.jpeg) 

### Compute Unit
![CU](img/NOOB_GPU_CU.jpeg) 


### (Global):
- Global Data Memory (think DRAM) 
- Global Instruction/Program Memory
### GPU
- Device Control Register - stores metadata of how kernels should be executed by GPU, e.g., how many threads for kernel that was launched
- Block Dispatcher - organizes threads into blocks that can be executed in parallel on a CU and dispatches these blocks to available CUs
    - Blocks that can be launched - as many as needed for the kernel workload (queued if all CUs are taken up)
- Memory Controller - coordinates global memory accesses from CUs
- ### Compute Unit (x4)
    - Wavefront Dispatcher - dispatches wavefronts (64 threads/wave) to SIMD units 
    - Scheduler
        - Considers a wave from one of the SIMD units for execution, selected in a round-robin fashion between SIMDs
        - Issues up to one instruction per wavefront on the selected SIMD
    - Instruction Decoder - breaks down an instruction into opcode, source/destination registers, immediate, etc.
    - ###  SIMD Unit (x4/CU)
        - Holds up to one wavefront at a time
            - One instruction takes 4 clock cycles to finish for a wavefront, since the SIMD is 16-wide.
        - Instruction Buffer
            - Holds decoded instructions for one wavefront
            - For just one wavefront/SIMD, this is unnecessary, but it is effective if more wavefronts per SIMD are added in the future.
        - Program Counter
        - ALU (16 lanes)
        - Load/Store Unit (16)
        - Vector Register File - Registers to store data for up to 1 wavefront
