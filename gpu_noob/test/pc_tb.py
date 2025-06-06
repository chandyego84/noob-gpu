import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from cocotb.result import TestFailure

@cocotb.test()
async def test_pc_basic(dut):
    """Test GPU Program Counter basic functionality"""

    # Start clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    # Reset DUT
    dut.rst.value = 1
    dut.update_pc.value = 0
    dut.dispatch_new_wave.value = 0
    dut.active_context.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    # All PCs should be zero after reset
    for ctx in range(5):
        dut.active_context.value = ctx
        await RisingEdge(dut.clk)
        assert dut.current_pc.value == 0, f"PC[{ctx}] not zero after reset"

    # Dispatch new wave to context 2
    dut.active_context.value = 2
    dut.dispatch_new_wave.value = 1
    await RisingEdge(dut.clk)
    dut.dispatch_new_wave.value = 0
    await RisingEdge(dut.clk)
    assert dut.current_pc.value == 0, "PC[2] should be zero after dispatch"

    # Update PC for context 2
    dut.update_pc.value = 1
    await RisingEdge(dut.clk)
    dut.update_pc.value = 0
    await RisingEdge(dut.clk)
    assert dut.current_pc.value == 1, "PC[2] should increment to 1"

    # Switch to context 3, dispatch new wave
    dut.active_context.value = 3
    dut.dispatch_new_wave.value = 1
    await RisingEdge(dut.clk)
    dut.dispatch_new_wave.value = 0
    await RisingEdge(dut.clk)
    assert dut.current_pc.value == 0, "PC[3] should be zero after dispatch"

    # Update PC for context 3 twice
    for _ in range(2):
        dut.update_pc.value = 1
        await RisingEdge(dut.clk)
        dut.update_pc.value = 0
        await RisingEdge(dut.clk)
    assert dut.current_pc.value == 2, "PC[3] should increment to 2"

    # Switch back to context 2, verify value
    dut.active_context.value = 2
    await RisingEdge(dut.clk)
    assert dut.current_pc.value == 1, "PC[2] should still be 1"

    # Check context 0 is still zero
    dut.active_context.value = 0
    await RisingEdge(dut.clk)
    assert dut.current_pc.value == 0, "PC[0] should still be 0"
