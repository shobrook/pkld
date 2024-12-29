# Standard library
import os
from pathlib import Path
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
    memory_cache = {}

    def decorator(f: callable):
        def decorated(*args, **kwargs) -> any:
            if store == "memory":
                # Use file path as cache key
                cache_key = (f.__name__ + '_' +
                             get_cache_fp(f, args, kwargs=kwargs).name)

                # Cached output exists, use it
                if cache_key in memory_cache:
                    print_log(f"{f.__name__}: Using output cached in-memory")
                    return memory_cache[cache_key]

                # Execute function and cache output
                output = f(*args, **kwargs)
                memory_cache[cache_key] = output
                print_log(f"{f.__name__}: Cached output in-memory")

                return output
            elif store == "disk":
                # Build full file path for cached output
                fn_dir = get_parent_dir(f)
                full_cache_dir = Path(
                    cache_dir or GLOBAL_CACHE_DIR or fn_dir / CACHE_DIR
                )
                full_cache_fp = Path(
                    cache_fp
                    or get_cache_fp(f, args, kwargs=kwargs, branch_factor=branch_factor)
                )
                full_cache_fp = full_cache_dir / full_cache_fp

                # Cached output exists, use it
                if os.path.isfile(full_cache_fp) and not overwrite:
                    try:
                        print_log(
                            f"{f.__name__}: Using output cached in {full_cache_fp}"
                        )
                        return get_cached_output(full_cache_fp)
                    except (UnpicklingError, MemoryError, EOFError) as e:
                        print_log(
                            f"\tFailed to retrieve cached output. Re-executing function."
                        )

                # Create cache directory if it doesn't exist
                full_cache_fp.parent.mkdir(parents=True, exist_ok=True)

                # Execute function and cache output
                output = f(*args, **kwargs)
                cache_output(output, full_cache_fp)
                print_log(f"{f.__name__}: Cached output in {full_cache_fp}")

                return output
            else:
                raise ValueError(
                    "Invalid value for `store`. Must be 'disk' or 'memory'."
                )

        return decorated

    return decorator
