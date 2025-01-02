# Standard library
import os
import time
import pickle
import asyncio
import threading
from pathlib import Path
from shutil import rmtree
from collections import defaultdict
from typing import Literal, Optional, Tuple

# Local
try:
    from marinate.utils import (
        get_cache_fp,
        get_cache_dir,
        get_logger,
        get_file_lock,
    )
except ImportError:
    from utils import (
        get_cache_fp,
        get_cache_dir,
        get_logger,
        get_file_lock,
    )


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
    memory_cache = defaultdict(dict)
    cache_lock = threading.Lock()

    def decorator(f: callable):
        def get_from_memory_cache(args: tuple, kwargs: dict) -> Tuple[any, bool]:
            start = time.time()

            cache_key = f.__name__
            cache_subkey = get_cache_fp(f, args, kwargs=kwargs).stem

            with cache_lock:
                if cache_subkey in memory_cache[cache_key]:
                    output = memory_cache[cache_key][cache_subkey]
                    duration = time.time() - start
                    print_log(
                        f"{f.__name__}: Used output cached in-memory (took {duration:.2f}s)"
                    )
                    return output, True

            return None, False

        def add_to_memory_cache(output: any, args: tuple, kwargs: dict):
            start = time.time()

            cache_key = f.__name__
            cache_subkey = get_cache_fp(f, args, kwargs=kwargs).stem

            with cache_lock:
                memory_cache[cache_key][cache_subkey] = output
                duration = time.time() - start
                print_log(
                    f"{f.__name__}: Cached output in-memory (took {duration:.2f}s)"
                )

        def get_from_disk_cache(cache_fp: Path) -> Tuple[any, bool]:
            start = time.time()
            with get_file_lock(cache_fp):
                # Cached output exists, use it
                if os.path.isfile(cache_fp) and not overwrite:
                    try:
                        with open(str(cache_fp), "rb") as file:
                            output = pickle.load(file)
                            duration = time.time() - start
                            print_log(
                                f"{f.__name__}: Using output cached in {cache_fp} (took {duration:.2f}s)"
                            )
                            return output, True
                    except (pickle.UnpicklingError, MemoryError, EOFError) as e:
                        print_log(
                            f"{f.__name__}: Failed to retrieve cached output. Re-executing function."
                        )

            return None, False

        def add_to_disk_cache(output: any, cache_fp: Path):
            start = time.time()
            with get_file_lock(cache_fp):
                with open(str(cache_fp), "wb") as file:
                    pickle.dump(output, file)
                    duration = time.time() - start
                    print_log(
                        f"{f.__name__}: Executed and cached output in {cache_fp} (took {duration:.2f}s)"
                    )

        async def async_decorated(*args, **kwargs) -> any:
            if store == "memory":
                output, is_cached = get_from_memory_cache(args, kwargs)
                if not is_cached:
                    output = await f(*args, **kwargs)
                    add_to_memory_cache(output, args, kwargs)

                return output
            elif store == "disk":
                cache_file_path = get_cache_fp(
                    f, args, kwargs, cache_dir, cache_fp, branch_factor
                )
                cache_file_path.parent.mkdir(parents=True, exist_ok=True)

                output, is_cached = get_from_disk_cache(cache_file_path)
                if not is_cached:
                    output = await f(*args, **kwargs)
                    add_to_disk_cache(output, cache_file_path)

                return output
            elif store == "both":
                pass

            raise ValueError(
                "Invalid value for `store`. Must be 'disk', 'memory', or 'both'."
            )

        def sync_decorated(*args, **kwargs) -> any:
            if store == "memory":
                output, is_cached = get_from_memory_cache(args, kwargs)
                if not is_cached:
                    output = f(*args, **kwargs)
                    add_to_memory_cache(output, args, kwargs)

                return output
            elif store == "disk":
                cache_file_path = get_cache_fp(
                    f, args, kwargs, cache_dir, cache_fp, branch_factor
                )
                cache_file_path.parent.mkdir(parents=True, exist_ok=True)

                output, is_cached = get_from_disk_cache(cache_file_path)
                if not is_cached:
                    output = f(*args, **kwargs)
                    add_to_disk_cache(output, cache_file_path)

                return output
            elif store == "both":
                pass

            raise ValueError(
                "Invalid value for `store`. Must be 'disk', 'memory', or 'both'."
            )

        def decorated(*args, **kwargs) -> any:
            if asyncio.iscoroutinefunction(f):
                return async_decorated(*args, **kwargs)

            return sync_decorated(*args, **kwargs)

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
                fn_cache = get_cache_dir(f, cache_dir)
                with get_file_lock(fn_cache):
                    if fn_cache.exists():
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
