def safe_int(val):
    try:
        v = int(val)

        if hasattr(val, 'is_resolvable') and not val.is_resolvable:
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
