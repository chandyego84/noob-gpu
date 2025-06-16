import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from cocotb.utils import get_sim_time
from common import safe_int, signed_int

THREADS = 320 # 5 BLOCKS (1 more than there are CUs)
BLOCK_DIM = 64

async def log_signals(dut):
    cycle = 0
    dut._log.info(f"NUM_CORES = {int(dut.NUM_CORES.value)}")

    while True:
        await RisingEdge(dut.clk)
        curr_ns = get_sim_time(units="ns")
        dispatched = safe_int(dut.blocks_dispatched.value)
        blocks_done = safe_int(dut.blocks_done.value)
        kernel_done = safe_int(dut.kernel_done.value)
        enable = safe_int(dut.enable.value)
        rst = safe_int(dut.rst.value)
        num_threads = safe_int(dut.num_threads.value)
        block_dim = safe_int(dut.block_dim.value)
        num_blocks = safe_int(dut.num_blocks.value)
        dut._log.info(
            f"\n---- CLOCK CYCLE: {cycle} @ {curr_ns} ns ----\n"
            f"dispatched={dispatched}\n"
            f"blocks_done={blocks_done} kernel_done={kernel_done}\n"
            f"enable={enable} rst={rst}\n"
            f"num_threads={num_threads} block_dim={block_dim} num_blocks={num_blocks}\n"
        )

        for i in range(int(dut.NUM_CORES.value)):
            dut._log.info(
                f"  Core {i}: start={(dut.core_start[i].value)} "
                f"core_ready={(dut.core_ready[i].value)} "
                f"block_id={signed_int(dut.core_block_id[i].value)} "
                f"done={(dut.core_done[i].value)}"
            )
        cycle += 1

@cocotb.test()
async def test_block_dispatch(dut):
    """
    Test block dispatcher module
    """

    # start 100MHz clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    cocotb.start_soon(log_signals(dut))

    # init reset
    dut.rst.value = 1
    dut.enable.value = 1
    dut.num_threads.value = THREADS
    dut.block_dim.value = BLOCK_DIM
    dut.core_done.value = 0 # none of the cores are done at start (duh)
    await Timer(20, units="ns")  # Hold reset for a while
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    # test -- after rst, all blockIDs should be 0 and no blocks dispatched
    for i in range(int(dut.NUM_CORES.value)):
        assert signed_int(dut.core_block_id[i].value) == signed_int(dut.INVALID_BLOCK_ID), f"After reset, block_id for CU{i} should be {signed_int(dut.INVALID_BLOCK_ID)}"
    assert safe_int(dut.blocks_dispatched.value) == 0, "After reset, blocks_dispatched should be 0"
    assert safe_int(dut.blocks_done.value) == 0, "After reset, blocks_done should be 0"
    assert safe_int(dut.kernel_done.value) == 0, "After reset, kernel_done should be 0"

    # test -- all cores have correct assigned block
    await RisingEdge(dut.clk)
    for i in range(int(dut.NUM_CORES.value)):
        assert safe_int(dut.core_block_id[i].value) == i, f"On first dispatch, CU{i} should have block_id {i}"
    
    # test -- CU0 is done executing its block
    dut.core_done[0].value = 1
    await RisingEdge(dut.clk) # core done set
    await RisingEdge(dut.clk) # core done processed
    dut.core_done[0].value = 0
    assert safe_int(dut.blocks_done.value) == 1, "CU0 is done, blocks_done should be 1"

    # test -- CU0 was given another block, since it completed its last one
    await RisingEdge(dut.clk) # core given new block
    assert safe_int(dut.core_block_id[0].value) == 4, f"CU0 should have been assigned new block_id 4, Actual block_id: {safe_int(dut.core_block_id[0].value)}" 
    assert safe_int(dut.blocks_dispatched.value) == 5, f"5 blocks should have been dispatched, got {safe_int(dut.blocks_dispatched.value)} instead"
    assert safe_int(dut.core_start[0]) == 1, "CU0 was recently assigned block 4 and start status should be 1"

    ## test -- finish all of the blocks now!
    for i in range(int(dut.NUM_CORES.value)):
        dut.core_done[i].value = 1
        await RisingEdge(dut.clk) # core done set
        await RisingEdge(dut.clk) # core done processed
        dut.core_done[i].value = 0
        assert safe_int(dut.blocks_done.value) == i + 2, f"CU{i} is done, blocks_done should be {i + 2}" # +1 (C0 finished a block before this), +1 (this core finished its block)
        assert safe_int(dut.core_ready[i].value) == 1, f"CU{i} is done, ready state should be 1"
        assert safe_int(dut.core_start[i].value) == 0, f"CU{i} is done, start state should be 0" 

    # test -- kernel is done
    await RisingEdge(dut.clk)
    assert safe_int(dut.kernel_done) == 1, "All blocks of kernel are done, kernel_done should be 1"