
def format_number(number, precision=2):
    return f"{number:.{precision}f}"

def validate_input(value, min_val=None, max_val=None):
    if min_val is not None and value < min_val:
        raise ValueError(f"Value {value} is below minimum {min_val}")
    if max_val is not None and value > max_val:
        raise ValueError(f"Value {value} is above maximum {max_val}")
    return True
