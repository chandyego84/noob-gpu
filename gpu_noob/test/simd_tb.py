import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from common import *

BLOCK_DIM = 64
WAVE_SIZE = 32
NUM_THREADS = 32 # number of threads to launch for this test
LANE_WIDTH = 16
DATA_WIDTH = 64
ADDR_WIDTH = 7  # 128 locations for data memory

# --- Simulate the kernel in one SIMD over two wavecycles ---
### Calculate global_id ###
# MUL R4, %blockIdx, %blockDim # 0 * 64
# ADD R4, R4, %threadIdx ; i = blockIdx * blockDim + threadIdx 


### Placing data memory addresses of matrices in registers ###
# CONST R5, #0 ; baseA (matrix A base address) 
# CONST R6, #32 ; baseB (matrix B base address) 
# CONST R7, #64 ; baseC (matrix C base address) 

### Calculating A[i] address and getting from data memory ###
# ADD R8, R5, R4 ; addr(A[i]) = baseA + i 
# LDR R8, R8 ; load A[i] from global memory 

### Calculating B[i] address and getting from data memory ###
# ADD R9, R6, R4 ; addr(B[i]) = baseB + i 
# LDR R9, R9 ; load B[i] from global memory 

### Addition of A[i], B[i] ###
# ADD R10, R8, R9 ; C[i] = A[i] + B[i] 

### Calculating C[i] and storing computed sum in data memory ###
# ADD R11, R7, R4 ; addr(C[i]) = baseC + i 
# STR R10, R11 ; store C[i] in global memory 

# RET ; end of kernel

A = [i for i in range(WAVE_SIZE)]
B = [i for i in range(WAVE_SIZE)]
C_expected = [A[i] + B[i] for i in range(WAVE_SIZE)]

async def log_signals(dut, DEBUG=False):
    cycle = 0
    while True:
        await RisingEdge(dut.clk)
        if (DEBUG):
            dut._log.info(
                f"\n---- CYCLE {cycle} ----\n"
                f"INSTRUCTION={safe_hex(dut.instruction.value)}, PC={safe_int(dut.curr_pc.value)}, PC_OUT={safe_int(dut.pc_out.value)}\n"
                f"OPCODE={get_state(OpCode, safe_int(dut.op_code.value))}, Total_Wave_Cycles={safe_int(dut.TOTAL_WAVE_CYCLES.value)}\n"
                
                f"rst={safe_int(dut.rst.value)} enable={safe_int(dut.enable.value)}\n"
                f"FETCHER_STATE={get_state(Fetcher_State, dut.fetcher_state.value)}\n"
                f"SIMD_STATE={get_state(SIMD_State, dut.simd_state.value)} wave_id={safe_int(dut.wave_id.value)}, wave_cycle={safe_int(dut.curr_wave_cycle.value)}\n"
                f"simd_ready={safe_int(dut.simd_ready.value)}, simd_start={safe_int(dut.simd_start.value)}, simd_working={safe_int(dut.simd_working.value)}, simd_done={safe_int(dut.simd_done.value)}\n"
                f"Rd={safe_int(dut.rd.value)}, Rm={safe_int(dut.rm.value)}, Rn={safe_int(dut.rn.value)}\n"
            )

            dut._log.info("------------------------------------------------------- \n"
                f"PROG_MEM_READ={safe_int(dut.prog_mem_read_valid.value)} "
                f"PROG_MEM_ACK={safe_int(dut.prog_mem_read_ack.value)}\n"
                f"DATA_MEM_READ={safe_int(dut.MEM_READ.value)} DATA_MEM_WRITE={safe_int(dut.MEM_WRITE.value)}\n"
                f"REG_WRITE={safe_int(dut.REG_WRITE.value)}\n"
                f"------------------------------------------------------- \n")

            dut._log.info("------------------------------------------------------- \n")
            for lane in range(LANE_WIDTH):
                dut._log.info(
                    f"  Lane {safe_int(dut.lane_id[lane])}: "
                    f"ThreadIdx: {safe_int(dut.out_thread_id_x[lane].value)} "
                    #f"LSU_State: {get_state(LSU_State, dut.lsu_state[lane].value)} "
                    f"rm_data={safe_int(dut.rm_data[lane].value)}, rn_data={safe_int(dut.rn_data[lane].value)} " 
                    f"ALU_Out: {safe_int(dut.alu_out[lane].value)} "
                    f"mem_read_valid={safe_int(dut.mem_read_valid[lane].value)} "
                    f"mem_write_valid={safe_int(dut.mem_write_valid[lane].value)} "
                    f"mem_addr={safe_int(dut.mem_addr[lane].value)} "
                    f"mem_write_data={safe_int(dut.mem_write_data[lane].value)} "
                    f"mem_read_data={safe_int(dut.mem_read_data[lane].value)}"
                )
            dut._log.info("\n ------------------------------------------------------- \n")
        
        else:
            print(f"Cycle: {cycle}")
        
        cycle += 1
    
class ProgramMemoryModel:
    def __init__(self, dut):
        self.dut = dut
        self.mem = [0] * 64

    async def run(self):
        while True:
            await RisingEdge(self.dut.clk)
            try:
                # signaled for a prog_mem read
                valid = safe_int(self.dut.prog_mem_read_valid.value)
            except Exception:
                valid = 0
            if valid == 1:
                addr = safe_int(self.dut.prog_mem_addr.value)
                self.dut.prog_mem_read_data.value = self.mem[addr]
                self.dut.prog_mem_read_ack.value = 1

            else:
                self.dut.prog_mem_read_ack.value = 0

class DataMemoryModel:
    def __init__(self, dut):
        self.dut = dut
        self.mem = [0] * (2**ADDR_WIDTH)

    async def run(self):
        while True:
            await RisingEdge(self.dut.clk)
            for lane in range(LANE_WIDTH):
                # LOAD
                try:
                    valid = safe_int(self.dut.mem_read_valid[lane].value)
                except Exception:
                    valid = 0
                if valid == 1:
                    addr = safe_int(self.dut.mem_addr[lane].value)
                    self.dut.mem_read_data[lane].value = self.mem[addr]
                    self.dut.data_mem_read_ack[lane].value = 1
                else:
                    self.dut.data_mem_read_ack[lane].value = 0

                # STORE
                try:
                    valid = safe_int(self.dut.mem_write_valid[lane].value)
                except Exception:
                    valid = 0
                if valid == 1:
                    addr = safe_int(self.dut.mem_addr[lane].value)
                    data = safe_int(self.dut.mem_write_data[lane].value)
                    self.mem[addr] = data
                    self.dut.data_mem_write_ack[lane].value = 1
                else:
                    self.dut.data_mem_write_ack[lane].value = 0
    
    def dump(self, line_width = 4):
        """Print memory contents as Addr[N]: VALUE for each address."""
        mem_size = len(self.mem)

        print("\nData Memory Dump:")
        print("-" * 30)

        for addr in range(mem_size):
            if addr % line_width == 0:
                if addr != 0:
                    print()
                    
            if (addr == NUM_THREADS * 2):
                print("-"*15 + "Result addresses" + "-"*15)

            print(f"M[{addr:3}]: {self.mem[addr]:<5}", end="  ")

    print("\n" + "-" * 30)

@cocotb.test()
async def test_simd_vector_add(dut):
    # Logger
    cocotb.start_soon(log_signals(dut))

    # Initialize models
    data_mem = DataMemoryModel(dut)
    prog_mem = ProgramMemoryModel(dut)
    cocotb.start_soon(data_mem.run())
    cocotb.start_soon(prog_mem.run())
    
    # Start clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
        
    # Initialize data memory
    for i in range(NUM_THREADS):
        data_mem.mem[i] = i # Vector A: 0-31
        data_mem.mem[i+NUM_THREADS] = i # Vector B: 32-63
    
    data_mem.dump()
    
    # Load vector addition program
    instructions = [
        0b000100_0000100_0011100_0011101_00000, # MUL R4, R28, R29 
        0b000010_0000100_0000100_0011110_00000, # ADD R4, R4, R30
        0b001000_0000101_0000000_0000000_00000, # CONST R5, 0
        0b001000_0000110_0000000_0000001_00000, # CONST R6, 32
        0b001000_0000111_0000000_0000010_00000, # CONST R7, 64
        0b000010_0001000_0000101_0000100_00000, # ADD R8, R5, R4
        0b000000_0001000_0001000_0000000_00000, # LDUR R8, R8
        0b000010_0001001_0000110_0000100_00000, # ADD R9, R6, R4
        0b000000_0001001_0001001_0000000_00000, # LDUR R9, R9
        0b000010_0001010_0001000_0001001_00000, # ADD R10, R8, R9
        0b000010_0001011_0000111_0000100_00000, # ADD R11, R7, R4
        0b000001_0000000_0001011_0001010_00000, # STUR R10, R11
        0b111111_0000000_0000000_0000000_00000 # RET
    ]
    for i, instr in enumerate(instructions):
        prog_mem.mem[i] = instr
    
    # set initial state
    # Reset
    dut.rst.value = 1
    dut.enable.value = 1
    await Timer(20, units="ns")
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    dut.num_threads.value = NUM_THREADS
    dut.block_dim.value = BLOCK_DIM
    dut.block_id.value = 0
    dut.wave_id.value = 0
    dut.num_waves_in_block.value = 1
    dut.simd_ready.value = 0
    dut.simd_start.value = 1
    dut.simd_working.value = 1
    await RisingEdge(dut.clk)
    dut.simd_start.value = 0
    await RisingEdge(dut.clk)

    while dut.simd_done.value != 1:
        await RisingEdge(dut.clk)    
    
    data_mem.dump()

    for i in range(NUM_THREADS):
        actual = data_mem.mem[NUM_THREADS*2 + i]
        expected = i + i  # A[i] + B[i]
        assert actual == expected, f"Mismatch at {i}: {actual} vs {expected}"

    dut._log.info("SIMD vector addition kernel test passed for all lanes.")
