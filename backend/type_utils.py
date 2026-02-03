"""
Type Conversion Utilities for GlucoLumin
Handles NumPy to Python type conversion for database compatibility
"""
import numpy as np
from typing import Any


def numpy_to_python(obj: Any) -> Any:
    """
    Convert NumPy types to Python native types for database compatibility.
    
    PostgreSQL/SQLAlchemy cannot serialize NumPy types directly.
    This function recursively converts all NumPy types in the input.
    
    Args:
        obj: Any object (scalar, dict, list, or NumPy type)
        
    Returns:
        Object with all NumPy types converted to Python natives
    """
    # Handle NumPy integer types
    if isinstance(obj, np.integer):
        return int(obj)
    
    # Handle NumPy floating types
    elif isinstance(obj, np.floating):
        return float(obj)
    
    # Handle NumPy boolean types
    elif isinstance(obj, np.bool_):
        return bool(obj)
    
    # Handle NumPy arrays
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    
    # Handle dictionaries (recursive)
    elif isinstance(obj, dict):
        return {k: numpy_to_python(v) for k, v in obj.items()}
    
    # Handle lists (recursive)
    elif isinstance(obj, list):
        return [numpy_to_python(item) for item in obj]
    
    # Handle tuples (recursive, return as tuple)
    elif isinstance(obj, tuple):
        return tuple(numpy_to_python(item) for item in obj)
    
    # Return as-is for other types (str, int, float, None, etc.)
    return obj
