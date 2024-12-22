# Standard library
import os
from functools import cache
from typing import Literal, Optional

# Local
try:
    from marinate.utils import (
        get_file_path,
        get_cache_key,
        get_cached_output,
        cache_output,
        get_logger,
    )
except ImportError:
    from utils import (
        get_file_path,
        get_cache_key,
        get_cached_output,
        cache_output,
        get_logger,
    )


GLOBAL_CACHE_DIR = None


def set_cache_dir(cache_dir: str):
    global global_cache_dir
    global_cache_dir = cache_dir


def marinate(
    cache_file: Optional[str] = None,
    cache_dir: Optional[str] = None,
    overwrite: bool = False,
    store: Literal["disk", "memory"] = "disk",
    verbose: bool = False,
):
    print_log = get_logger(verbose)

    # Validate store parameter
    if store not in {"disk", "memory"}:
        raise ValueError("Invalid value for 'store'. Must be 'disk' or 'memory'.")

    cache_dir = cache_dir or global_cache_dir

    def decorator(f: callable):
        def decorated(*args, **kwargs) -> any:
            if store == "memory":
                print_log(f"Using in-memory cache for {f.__name__}")
                return cache(f)(*args, **kwargs)

            cache_key = get_cache_key(f, args, kwargs)
            fn_file = f.__globals__["__file__"]
            file_path = get_file_path(fn_file, cache_key, cache_file, cache_dir)

            # Use cache if file exists and isn't invalidated
            if os.path.isfile(file_path) and not overwrite:
                print_log(f"Using cached output for {f.__name__} in {file_path}")
                return get_cached_output(file_path)

            # Execute function and cache output
            output = f(*args, **kwargs)
            cache_output(output, file_path)
            print_log(f"Cached output for {f.__name__} in {file_path}")

            return output

        return decorated

    return decorator
