import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from cocotb.utils import get_sim_time
from common import safe_int, signed_int

SIMD_EXECUTE = 0b101

async def pc_in_wire(dut):
    while True:
        await RisingEdge(dut.clk)
        dut.pc_in.value = dut.pc_out.value

async def log_signals(dut):
    cycle = 0
    dut._log.info(f"PROGRAM_MEM_ADDR_WIDTH = {safe_int(dut.PROGRAM_MEM_ADDR_WIDTH.value)}")

    while True:
        await RisingEdge(dut.clk)
        curr_ns = get_sim_time(units="ns")
        
        enable = safe_int(dut.enable.value)
        rst = safe_int(dut.rst.value)
        dispatch_new_wave = safe_int(dut.DISPATCH_NEW_WAVE.value)
        pc_in = safe_int(dut.pc_in.value)
        pc_out = safe_int(dut.pc_out.value)
        simd_state = safe_int(dut.simd_state.value)

        dut._log.info(
            f"\n---- CLOCK CYCLE: {cycle} @ {curr_ns} ns ----\n"
            f"enable={enable} rst={rst}\n"
            f"NEW_WAVE={dispatch_new_wave} simd_state={simd_state}\n"
            f"pc_in={pc_in} pc_out={pc_out}\n"
        )

        cycle += 1

@cocotb.test()
async def test_pc(dut):
    """Test program counter (PC) module functionality."""

    # Start the clock (100 MHz)
    clock = Clock(dut.clk, 10, units="ns")  # 10ns period = 100 MHz
    cocotb.start_soon(clock.start())
    cocotb.start_soon(pc_in_wire(dut))
    cocotb.start_soon(log_signals(dut))

    # Initial reset
    dut.rst.value = 1
    dut.enable.value = 1
    dut.simd_state.value = 0
    dut.DISPATCH_NEW_WAVE.value = 0
    await Timer(20, units="ns")  # Hold reset for a while
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    # Check reset behavior: all internal PCs should be 0
    expected = 0
    actual = safe_int(dut.pc_out.value)
    assert expected == actual, f"On RST, pc_out should be {expected}, got {actual}"

    # test -- dispatch new wave
    dut.DISPATCH_NEW_WAVE.value = 1
    await RisingEdge(dut.clk) # new wave signal updated
    dut.DISPATCH_NEW_WAVE.value = 0
    await RisingEdge(dut.clk) # new wave signal processed
    expected = 0
    actual = safe_int(dut.pc_out.value)
    assert expected == actual, f"New wave dispatched, pc_out should be {expected}, got {actual}"
    expected = 0
    actual = safe_int(dut.pc_in.value)
    assert expected == actual, f"New wave dispatched, pc_in should be {expected}, got {actual}"
    
    # test -- update pc (arbitrary amount of PC updates)
    for i in range(1, 5):
        dut.simd_state.value = SIMD_EXECUTE
        await RisingEdge(dut.clk) # EXECUTE state
        dut.simd_state.value = 0
        await RisingEdge(dut.clk) # back to IDLE
        expected = i
        actual = safe_int(dut.pc_out.value)
        assert expected == actual, f"Update {i}: pc_out expected = {expected}, got {actual}"
    
    # test -- assuming SIMD finished current wave, then  
    #  new wave dispatched (reset PC to 0)
    dut.simd_state.value = 0
    dut.DISPATCH_NEW_WAVE.value = 1
    await RisingEdge(dut.clk) # signals updated
    dut.DISPATCH_NEW_WAVE.value = 0
    await RisingEdge(dut.clk) # signals processed
    expected = 0
    actual = safe_int(dut.pc_out.value)
    assert expected == actual, f"New wave dispatched, pc_out expected = {expected}, got {actual}"
    await RisingEdge(dut.clk)