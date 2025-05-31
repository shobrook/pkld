# Standard library
import os
import time
import pickle
import asyncio
import threading
import inspect
from pathlib import Path
from shutil import rmtree
from collections import defaultdict
from typing import Literal, Optional, Tuple

# Local
try:
    from pkld.utils import (
        get_cache_fp,
        get_cache_dir,
        get_logger,
        get_file_lock,
        process_signature,
        GLOBAL_CACHE_DIR,
)
except ImportError:
    from utils import (
        get_cache_fp,
        get_cache_dir,
        get_logger,
        get_file_lock,
        GLOBAL_CACHE_DIR,
    )


######
# MAIN
######


def set_cache_dir(cache_dir: str):
    global GLOBAL_CACHE_DIR
    GLOBAL_CACHE_DIR = cache_dir


def pkld(
    func=None,
    cache_fp: Optional[str] = None,
    cache_dir: Optional[str] = None,
    disabled: bool = False,
    store: Literal["disk", "memory", "both"] = "disk",
    verbose: bool = False,
    overwrite: bool = False,
    max_fn_len: int = 128,
):
    print_log = get_logger(verbose)
    memory_cache = defaultdict(dict)
    overwrite_semi_cache = defaultdict(set)
    cache_lock = threading.Lock()

    def decorator(f: callable):
        def get_from_memory_cache(args: tuple, kwargs: dict) -> Tuple[any, bool]:
            start = time.time()

            cache_key = f.__name__
            cache_subkey = get_cache_fp(f, args, max_fn_len=max_fn_len, kwargs=kwargs).stem

            with cache_lock:
                if cache_subkey in memory_cache[cache_key] and not disabled:
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
            cache_subkey = get_cache_fp(f, args, max_fn_len=max_fn_len, kwargs=kwargs).stem

            with cache_lock:
                memory_cache[cache_key][cache_subkey] = output
                duration = time.time() - start
                print_log(
                    f"{f.__name__}: Cached output in-memory (took {duration:.2f}s)"
                )

        def add_to_overwrite_checker(args: tuple, kwargs: dict):
            cache_key = f.__name__
            cache_subkey = get_cache_fp(f, args, max_fn_len=max_fn_len, kwargs=kwargs).stem
            overwrite_semi_cache[cache_key].add(cache_subkey)

        def was_not_run_this_instance(args: tuple, kwargs: dict):
            cache_key = f.__name__
            cache_subkey = get_cache_fp(f, args, max_fn_len=max_fn_len, kwargs=kwargs).stem
            return cache_subkey not in overwrite_semi_cache[cache_key]

        def get_from_disk_cache(cache_fp: Path) -> Tuple[any, bool]:
            start = time.time()
            with get_file_lock(cache_fp):
                # Cached output exists, use it
                if os.path.isfile(cache_fp) and not disabled:
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
            arg_kwargs, args_iter = process_signature(f, args)
            overlap = set(arg_kwargs.keys()) & set(kwargs.keys())
            assert len(overlap) == 0, \
                (f'args and kwargs have overlapping keys: overlap: {overlap} | '
                 f'args: {arg_kwargs.keys()}, kwargs: {kwargs.keys()}')
            kwargs = {**arg_kwargs, **kwargs}
            args = tuple(args_iter)

            if store == "memory":
                output, is_cached = get_from_memory_cache(args, kwargs)
                if not is_cached:
                    output = await f(*args, **kwargs)
                    add_to_memory_cache(output, args, kwargs)

                return output
            elif store == "disk":
                cache_file_path = get_cache_fp(
                    f, args, kwargs, cache_dir, cache_fp, max_fn_len=max_fn_len
                )
                cache_file_path.parent.mkdir(parents=True, exist_ok=True)

                output, is_cached = get_from_disk_cache(cache_file_path)
                if not is_cached:
                    output = await f(*args, **kwargs)
                    add_to_disk_cache(output, cache_file_path)

                return output
            elif store == "both":
                output, is_cached = get_from_memory_cache(args, kwargs)
                if not is_cached:
                    cache_file_path = get_cache_fp(
                        f, args, kwargs, cache_dir, cache_fp, max_fn_len=max_fn_len
                    )
                    cache_file_path.parent.mkdir(parents=True, exist_ok=True)

                    output, is_cached = get_from_disk_cache(cache_file_path)
                    if not is_cached:
                        output = await f(*args, **kwargs)
                        add_to_disk_cache(output, cache_file_path)
                        add_to_memory_cache(output, args, kwargs)

                return output

            raise ValueError(
                "Invalid value for `store`. Must be 'disk', 'memory', or 'both'."
            )

        def sync_decorated(*args, **kwargs) -> any:
            arg_kwargs, args_iter = process_signature(f, args)
            overlap = set(arg_kwargs.keys()) & set(kwargs.keys())
            assert len(overlap) == 0, \
                (f'args and kwargs have overlapping keys: overlap: {overlap} | '
                 f'args: {arg_kwargs.keys()}, kwargs: {kwargs.keys()}')
            kwargs = {**arg_kwargs, **kwargs}
            args = tuple(args_iter)

            if store == "memory":
                output, is_cached = get_from_memory_cache(args, kwargs)

                if not is_cached:
                    output = f(*args, **kwargs)
                    add_to_memory_cache(output, args, kwargs)
                return output
            elif store == "disk":
                cache_file_path = get_cache_fp(
                    f, args, kwargs, cache_dir, cache_fp, max_fn_len=max_fn_len
                )
                cache_file_path.parent.mkdir(parents=True, exist_ok=True)
                cache_file_path = Path(str(cache_file_path).replace('?', ''))

                # output, is_cached = get_from_disk_cache(cache_file_path)

                if overwrite and was_not_run_this_instance(args, kwargs):
                    output = f(*args, **kwargs)
                    add_to_disk_cache(output, cache_file_path)
                    add_to_overwrite_checker(args, kwargs)
                else:
                    output, is_cached = get_from_disk_cache(cache_file_path)
                    if not is_cached:
                        output = f(*args, **kwargs)
                        add_to_disk_cache(output, cache_file_path)

                return output
            elif store == "both":
                output, is_cached = get_from_memory_cache(args, kwargs)
                if not is_cached:
                    cache_file_path = get_cache_fp(
                        f, args, kwargs, cache_dir, cache_fp, max_fn_len=max_fn_len
                    )
                    cache_file_path.parent.mkdir(parents=True, exist_ok=True)

                    if overwrite and was_not_run_this_instance(args, kwargs):
                        output = f(*args, **kwargs)
                        add_to_disk_cache(output, cache_file_path)
                        add_to_overwrite_checker(args, kwargs)
                    else:
                        output, is_cached = get_from_disk_cache(cache_file_path)
                        if not is_cached:
                            output = f(*args, **kwargs)
                            add_to_disk_cache(output, cache_file_path)
                        add_to_memory_cache(output, args, kwargs)
                return output

            raise ValueError(
                "Invalid value for `store`. Must be 'disk', 'memory', or 'both'."
            )

        def decorated(*args, **kwargs) -> any:
            if asyncio.iscoroutinefunction(f):
                return async_decorated(*args, **kwargs)

            return sync_decorated(*args, **kwargs)

        def clear_memory_cache():
            with cache_lock:
                if f.__name__ in memory_cache:
                    del memory_cache[f.__name__]

        def clear_disk_cache():
            fn_cache = get_cache_dir(f, cache_dir)
            with get_file_lock(fn_cache):
                if fn_cache.exists():
                    rmtree(fn_cache)

        def clear_cache():
            nonlocal memory_cache
            start = time.time()

            if store == "memory":
                clear_memory_cache()
                duration = time.time() - start
                print_log(
                    f"{f.__name__}: Cleared in-memory cache (took {duration:.2f}s)"
                )
            elif store == "disk":
                clear_disk_cache()
                duration = time.time() - start
                print_log(f"{f.__name__}: Cleared disk cache (took {duration:.2f}s)")
            elif store == "both":
                clear_memory_cache()
                clear_disk_cache()
                duration = time.time() - start
                print_log(
                    f"{f.__name__}: Cleared in-memory and disk cache (took {duration:.2f}s)"
                )

        decorated.clear = clear_cache
        return decorated

    if not func:
        return decorator

    return decorator(func)