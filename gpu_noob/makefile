### ARGS START ###
# ---- Simulator Selection ----
SIM ?= icarus

# ---- Wave file (FST file) ----
WAVE ?= 1

# ---- Language Selection ----
TOPLEVEL_LANG ?= verilog
### ARGS END ###

#############################################
# ---- Design and Testbench Configuration ----
# MODIFY DUT and TESTBENCH args to test other modules
DUT ?= BlockDispatch
TESTBENCH ?= block_dispatch_tb
#############################################
# ---- Source and Testbench Paths ----
# List all Verilog source files needed for simulation, including submodules
# Add more .v files as needed for your hierarchy
VERILOG_SOURCES = $(wildcard $(PWD)/modules/*.v)

# Top-level Verilog module name for cocotb
TOPLEVEL = $(DUT)

# Name of the Python testbench module
MODULE = $(TESTBENCH)
#############################################

export PYTHONPATH := $(PWD)/test:$(PYTHONPATH) # add python test dir to path
include $(shell cocotb-config --makefiles)/Makefile.sim # cocotb makefile include
