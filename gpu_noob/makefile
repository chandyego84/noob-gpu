SIM ?= icarus
WAVE ?= 0
TOPLEVEL_LANG ?= verilog

### Design and Testbench Configuration ###
DUT        ?= RegisterFile
TESTBENCH  ?= register_tb

TOPLEVEL	?= $(DUT)
MODULE 		?= $(TESTBENCH)

### Source and Testbench Paths ###
VERILOG_SOURCES = \
    $(PWD)/module/block_dispatch.v \
    $(PWD)/module/common_defs.v \
    $(PWD)/module/lsu.v \
    $(PWD)/module/pc.v \
    $(PWD)/module/register.v \
    $(PWD)/module/simd.v \
    $(PWD)/module/simd_controller.v \
    $(PWD)/module/wave_dispatch.v

PYTHONPATH := $(PWD)/test:$(PYTHONPATH)

### Include directories for Verilog ###
export IVERILOG_INCLUDE_DIRS = $(PWD)/module

### Waveform Output ###
ifeq ($(WAVE),1)
    export WAVES=1
    export COCOTB_VCD_WAVEFORM=wave.vcd
endif

### Export for cocotb ###
export PYTHONPATH
export VERILOG_SOURCES
export TOPLEVEL
export MODULE

include $(shell cocotb-config --makefiles)/Makefile.sim
