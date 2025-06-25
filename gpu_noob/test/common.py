from enum import Enum    

class SIMD_State(Enum):
    IDLE = 0
    FETCH = 1
    DECODE = 2
    REQUEST = 3
    WAIT = 4
    EXECUTE = 5
    UPDATE = 6
    DONE = 7

class LSU_State(Enum):
    IDLE = 0
    REQUESTING = 1
    WAITING = 2
    DONE = 3

class Fetcher_State(Enum):
    IDLE = 0
    FETCHING = 1
    FETCHED = 2

class RegWrite_Mux(Enum):
    REG_WRITE_LOAD = 0
    REG_WRITE_ALU = 1
    REG_WRITE_IMM = 2

def get_state(state_type: Enum, val):
    try:
        v = safe_int(val)
        if v == "X":
            return "X"
        
        return state_type(v).name
    
    except Exception:
        return "X"

def safe_int(val):
    try:
        v = int(val)

        if hasattr(val, 'is_resolvable') and not val.is_resolvable:
            return "X"
        
        return v
        
    except Exception:
        return "X"

def safe_hex(val):
    try:
        v = hex(val)

        if hasattr(val, 'is_resolvable'):
            return "X"
        
        return v
    
    except Exception:
        return "X"

def signed_int(val):
    try:
        if hasattr(val, 'signed_integer'):
            return val.signed_integer
        
        return val            
    
    except Exception:
        return "X"
