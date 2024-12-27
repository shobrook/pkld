# Standard library
import os
import pickle
from functools import cache
from pathlib import Path
from typing import Literal, Optional

# Local
try:
    from marinate.utils import (
        get_file_path,
        get_cache_fp,
        get_cached_output,
        cache_output,
        get_logger,
    )
except ImportError:
    from utils import (
        get_file_path,
        get_cache_fp,
        get_cached_output,
        cache_output,
        get_logger,
    )


GLOBAL_CACHE_DIR = None


def set_cache_dir(cache_dir: str):
    global global_cache_dir
    global_cache_dir = cache_dir


def marinate(
    cache_fp: Optional[str] = None,
    cache_dir: Optional[str] = None,
    overwrite: bool = False,
    store: Literal["disk", "memory"] = "disk",
    verbose: bool = False,
    cache_branches: int = 0,
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

            if cache_fp:
                func_fp = cache_fp
            else:
                func_fp = get_cache_fp(f, args, kwargs=kwargs,
                                       cache_branches=cache_branches)

            # I tried the below code but PyCharm says it's bad
            # if not cache_fp:
            #     cache_fp = get_cache_fp(f, args, kwargs)

            full_fp = Path(cache_dir) / func_fp
            if os.path.isfile(full_fp) and not overwrite:
                try:
                    print_log(f"Using cached output for {f.__name__} in {full_fp}")
                    return get_cached_output(full_fp)
                except (pickle.UnpicklingError, MemoryError, EOFError) as e:
                    print_log(f"\tRedoing function, error loading cache file {full_fp}: {e}")

            full_fp.parent.mkdir(parents=True, exist_ok=True)


            # if not cache_dir:
            #     fn_package = f.__globals__["__file__"]

            # file_path = get_file_path(fn_file, cache_key, cache_file, cache_dir)

            # Use cache if file exists and isn't invalidated
            # if os.path.isfile(file_path) and not overwrite:
            #     print_log(f"Using cached output for {f.__name__} in {file_path}")
            #     return get_cached_output(file_path)

            # Execute function and cache output
            output = f(*args, **kwargs)
            cache_output(output, full_fp)
            print_log(f"Cached output for {f.__name__} in {full_fp}")

            return output

        return decorated

    return decorator
