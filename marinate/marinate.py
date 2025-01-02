# Standard library
import os
import time
import threading
from pathlib import Path
from shutil import rmtree
from pickle import UnpicklingError
from typing import Literal, Optional

# Third-party
from filelock import FileLock

# Local
try:
    from marinate.utils import (
        get_cache_fp,
        get_cached_output,
        cache_output,
        get_logger,
        get_parent_dir,
        get_parent_file,
    )
except ImportError:
    from utils import (
        get_cache_fp,
        get_cached_output,
        cache_output,
        get_logger,
        get_parent_dir,
        get_parent_file,
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
    func=None,
    cache_fp: Optional[str] = None,
    cache_dir: Optional[str] = None,
    overwrite: bool = False,
    store: Literal["disk", "memory"] = "disk",
    verbose: bool = False,
    branch_factor: int = 0,
):
    print_log = get_logger(verbose)
    memory_cache = {}
    cache_lock = threading.Lock()

    def decorator(f: callable):
        def decorated(*args, **kwargs) -> any:
            start = time.time()

            if store == "memory":
                cache_key = f.__name__
                cache_subkey = get_cache_fp(f, args, kwargs=kwargs).stem

                # Cached output exists, use it
                with cache_lock:
                    if cache_key in memory_cache:
                        if cache_subkey in memory_cache[cache_key]:
                            output = memory_cache[cache_key][cache_subkey]
                            duration = time.time() - start
                            print_log(
                                f"{f.__name__}: Used output cached in-memory (took {duration:.2f}s)"
                            )
                            return output

                # Execute function (outside lock to prevent blocking)
                output = f(*args, **kwargs)

                # Cache the output
                with cache_lock:
                    memory_cache[cache_key] = output
                    duration = time.time() - start
                    print_log(
                        f"{f.__name__}: Executed and cached output in-memory (took {duration:.2f}s)"
                    )

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

                lock_fp = str(full_cache_fp) + ".lock"
                lock = FileLock(lock_fp)

                with lock:
                    # Cached output exists, use it
                    if os.path.isfile(full_cache_fp) and not overwrite:
                        try:
                            output = get_cached_output(full_cache_fp)
                            duration = time.time() - start
                            print_log(
                                f"{f.__name__}: Using output cached in {full_cache_fp} (took {duration:.2f}s)"
                            )
                            return output
                        except (UnpicklingError, MemoryError, EOFError) as e:
                            print_log(
                                f"{f.__name__}: Failed to retrieve cached output. Re-executing function."
                            )

                    # Create cache directory if it doesn't exist
                    full_cache_fp.parent.mkdir(parents=True, exist_ok=True)

                    # Execute function and cache output
                    output = f(*args, **kwargs)
                    cache_output(output, full_cache_fp)
                    duration = time.time() - start
                    print_log(
                        f"{f.__name__}: Executed and cached output in {full_cache_fp} (took {duration:.2f}s)"
                    )

                return output

            raise ValueError("Invalid value for `store`. Must be 'disk' or 'memory'.")

        def clear_cache():
            nonlocal memory_cache
            start = time.time()

            if store == "memory":
                with cache_lock:
                    if f.__name__ in memory_cache:
                        del memory_cache[f.__name__]
                        duration = time.time() - start
                        print_log(
                            f"{f.__name__}: Cleared in-memory cache (took {duration:.2f}s)"
                        )
            elif store == "disk":
                fn_file = get_parent_file(f).stem
                fn_dir = get_parent_dir(f)
                fn_cache = Path(cache_dir or GLOBAL_CACHE_DIR or fn_dir / CACHE_DIR)
                fn_cache /= Path(fn_file) / Path(f.__name__)

                lock_fp = str(fn_cache) + "/.lock"
                lock = FileLock(lock_fp)

                # Delete the fn_cache directory
                with lock:
                    if fn_cache.exists() and fn_cache.is_dir():
                        rmtree(fn_cache)
                        duration = time.time() - start
                        print_log(
                            f"{f.__name__}: Cleared disk cache (took {duration:.2f}s)"
                        )

        decorated.clear = clear_cache
        return decorated

    if not func:
        return decorator

    return decorator(func)
