# Standard library
import os
import pickle
import hashlib
from pathlib import Path
from typing import Optional, Union
import inspect
import warnings


#########
# HELPERS
#########


YELLOW = "\033[93m"
RESET = "\033[0m"


class PickleWrapWarning(UserWarning):
    pass


def hash_numpy_array(arr):
    """
    Function written by Claude 3.5 Sonnet

    Create a stable hash for a numpy array.

    Parameters:
        arr (np.ndarray): Input numpy array

    Returns:
        str: Hexadecimal hash string

    Note: This method ensures consistent hashing across sessions by:
        1. Converting the array to bytes in a consistent manner
        2. Using array flags to handle non-contiguous arrays
        3. Including array shape and dtype in the hash
    """
    # Ensure array is contiguous in memory

    import numpy as np

    if not arr.flags["C_CONTIGUOUS"]:
        arr = np.ascontiguousarray(arr)

    # Create a bytestring containing array metadata and content
    metadata = f"{arr.shape}_{arr.dtype}".encode("utf-8")
    content = arr.tobytes()

    # Combine metadata and content
    array_bytes = metadata + content

    # Create hash using SHA-256
    return hashlib.sha256(array_bytes).hexdigest()


def obj2str(val, max_len=16):
    try:
        import numpy as np
    except ModuleNotFoundError:
        np = None

    kwargs_str = ""
    if np and isinstance(val, np.ndarray):
        if val.size > 9_999_999:
            warnings.warn(
                f"Hashing a large ndarray ({val.shape}) to make the filepath, "
                f"may add considerable time to filepath generation.",
                PickleWrapWarning,
                stacklevel=2,
            )
        kwargs_str += hash_numpy_array(val)
        return kwargs_str
    elif isinstance(val, dict):
        for key2 in sorted(val.keys()):
            kwargs_str += obj2str(val[key2])
    elif isinstance(val, list):
        for val_ in val:
            kwargs_str += obj2str(val_)
    elif callable(val):
        kwargs_str += val.__name__
    else:
        if not isinstance(val, (str, int, float, bool, tuple, type(None))):
            val_type = type(val)
            warnings.warn(
                f"Including a {val_type} in the filepath, may create collisions "
                f"if not distinct: {str(val)}.",
                PickleWrapWarning,
                stacklevel=2,
            )
        kwargs_str += f"{val}_"

    if len(kwargs_str) > max_len:
        # 16 characters is enough for an under 1e-6 chance of collision among 10M values
        kwargs_str = hashlib.md5(kwargs_str.encode()).hexdigest()[:max_len]
    return kwargs_str


def get_parent_file(f: callable) -> Path:
    return Path(f.__globals__["__file__"])


def add_defaults_to_kwargs(f: callable, kwargs: dict) -> dict:
    # updates kwargs to include default values
    signature = inspect.signature(f)  # this should capture functools.partial changes?
    for k, v in signature.parameters.items():
        if v.default is v.empty:
            continue  # exclude args, only want kwargs

        if k not in kwargs:
            kwargs[k] = v.default

    return kwargs


def get_args_str(args: tuple) -> str:
    args_str = ""
    for arg in args:
        arg_str = obj2str(arg)
        args_str += f"_{arg_str}"

    return args_str[1:]


def get_kwargs_str(kwargs: dict) -> str:
    kwargs_str = ""
    for key, value in sorted(kwargs.items()):
        value_str = obj2str(value)
        kwargs_str += f"_{key[:3]}-{value_str}"

    return kwargs_str


######
# MAIN
######


def get_parent_dir(f: callable) -> Path:
    return get_parent_file(f).parent


def get_cache_fp(f: callable, *args, branch_factor: int = 0, **kwargs) -> Path:
    kwargs = add_defaults_to_kwargs(f, kwargs)
    cache_key = get_args_str(args) + get_kwargs_str(kwargs)

    fn_file = get_parent_file(f).name
    fn_name = f.__name__

    # Build cache file path: <filename_fn_belongs_to>/<fn_name>/<branch_index>/<cache_key>.pkl
    cache_fp = Path(fn_file) / Path(fn_name)
    if branch_factor > 0:
        hash_int = int(hashlib.md5(cache_key.encode()).hexdigest(), 16)
        dir_index = hash_int % branch_factor
        cache_fp /= str(dir_index)
    cache_fp /= f"{cache_key}.pkl"

    return cache_fp


def get_cached_output(path: Union[str, Path]) -> any:
    with open(path, "rb") as file:
        output = pickle.load(file)
        return output


def cache_output(output: any, path: Union[str, Path]):
    with open(path, "wb") as file:
        pickle.dump(output, file)


def get_logger(verbose: bool = False) -> callable:
    def log(s: str):
        if verbose:
            print(f"{YELLOW}marinate | {s}{RESET}")

    return log
