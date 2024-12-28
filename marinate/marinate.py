# Standard library
import os
from pathlib import Path
from functools import cache
from pickle import UnpicklingError
from typing import Literal, Optional

# Local
try:
    from marinate.utils import (
        get_cache_fp,
        get_cached_output,
        cache_output,
        get_logger,
        get_parent_dir,
    )
except ImportError:
    from utils import (
        get_cache_fp,
        get_cached_output,
        cache_output,
        get_logger,
        get_parent_dir,
    )


CACHE_DIR = ".picklejar"
GLOBAL_CACHE_DIR = None


######
# MAIN
######


def set_cache_dir(cache_dir: str):
    global GLOBAL_CACHE_DIR
    GLOBAL_CACHE_DIR = cache_dir


def marinate(
    cache_fp: Optional[str] = None,
    cache_dir: Optional[str] = None,
    overwrite: bool = False,
    store: Literal["disk", "memory"] = "disk",
    verbose: bool = False,
    branch_factor: int = 100,
):
    print_log = get_logger(verbose)

    # Validate store parameter
    if store not in {"disk", "memory"}:
        raise ValueError("Invalid value for 'store'. Must be 'disk' or 'memory'.")

    def decorator(f: callable):
        def decorated(*args, **kwargs) -> any:
            if store == "memory":
                # TODO: Implement our own in-memory cache using FPs
                print_log(f"{f.__name__}: Using output cached in-memory")
                return cache(f)(*args, **kwargs)

            # Build unique file path for function output
            fn_dir = get_parent_dir(f)  # Directory that f belongs to
            _cache_dir = Path(cache_dir or GLOBAL_CACHE_DIR or fn_dir / CACHE_DIR)
            _cache_fp = Path(
                cache_fp
                or get_cache_fp(f, args, kwargs=kwargs, branch_factor=branch_factor)
            )
            _cache_fp = _cache_dir / _cache_fp

            # Cached output exists, use it
            if os.path.isfile(_cache_fp) and not overwrite:
                try:
                    print_log(f"{f.__name__}: Using output cached in {_cache_fp}")
                    return get_cached_output(_cache_fp)
                except (UnpicklingError, MemoryError, EOFError) as e:
                    print_log(
                        f"\tFailed to retrieve cached output. Re-executing function."
                    )

            # Create cache directory if it doesn't exist
            _cache_fp.parent.mkdir(parents=True, exist_ok=True)

            # Execute function and cache output
            output = f(*args, **kwargs)
            cache_output(output, _cache_fp)
            print_log(f"{f.__name__}: Cached output in {_cache_fp}")

            return output

        return decorated

    return decorator
