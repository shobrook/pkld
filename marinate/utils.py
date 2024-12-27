# Standard library
import os
import pickle
import hashlib
from pathlib import Path
from typing import Optional, Union
import inspect
import warnings


YELLOW = "\033[93m"
RESET = "\033[0m"
CACHE_DIR = ".marinate" # TODO: change per final name



def get_file_path(
    fn_file: str,
    cache_key: Optional[str] = None,
    cache_file: Optional[str] = None,
    cache_dir: Optional[str] = None,
) -> str:
    file_path = cache_file or cache_key
    file_path = f"{file_path}.pkl" if not file_path.endswith(".pkl") else file_path

    if cache_dir:
        dir_path = cache_dir
    else:
        dir_path = os.path.dirname(fn_file)
        dir_path = os.path.join(dir_path, CACHE_DIR)

    if cache_file:
        return file_path

    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    return os.path.join(dir_path, file_path)

class PickleWrapWarning(UserWarning):
    pass


def hash_array(arr):
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

    if not arr.flags['C_CONTIGUOUS']:
        arr = np.ascontiguousarray(arr)

    # Create a bytestring containing array metadata and content
    metadata = f"{arr.shape}_{arr.dtype}".encode('utf-8')
    content = arr.tobytes()

    # Combine metadata and content
    array_bytes = metadata + content

    # Create hash using SHA-256
    return hashlib.sha256(array_bytes).hexdigest()



def obj2str(val, max_len=16):
    try:
        import numpy as np
    except ModuleNotFoundError:
        pass

    kwargs_str = ''
    if isinstance(val, np.ndarray):
        if val.size > 9_999_999:
            warnings.warn(f'Hashing a large ndarray ({val.shape}) to make the filepath, '
                          f'may add considerable time to filepath generation.',
                          PickleWrapWarning, stacklevel=2)
        kwargs_str += hash_array(val)
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
            warnings.warn(f'Including a {val_type} in the filepath, may create collisions '
                          f'if not distinct: {str(val)}.',
                          PickleWrapWarning, stacklevel=2)
        kwargs_str += f'{val}_'

    if len(kwargs_str) > max_len:
        # 16 characters is enough for an under 1e-6 chance of collision among 10M values
        kwargs_str = hashlib.md5(kwargs_str.encode()).hexdigest()[:max_len]
    return kwargs_str


def get_cache_fp(f: callable, *args, cache_branches: int=0, **kwargs) -> str:
    f_name = f.__name__

    # updates kwargs to include default values
    signature = inspect.signature(f) # this should capture functools.partial changes?
    for k, v in signature.parameters.items():
        if v.default is v.empty: continue # exclude args, only want kwargs
        if k not in kwargs: kwargs[k] = v.default

    fn = ''
    for v in args:
        v_str = obj2str(v)
        add = f'_{v_str}'
        fn += add
    fn = fn[1:]
    for k, v in sorted(kwargs.items()):
        v_str = obj2str(v)
        add = f'_{k[:3]}-{v_str}'
        fn += add
    fn += '.pkl'
    if cache_branches > 0:
        hash_int = int(hashlib.md5(fn.encode()).hexdigest(), 16)
        dir_idx = hash_int % cache_branches
        func_fp = Path(f_name) / str(dir_idx) / fn
    else:
        func_fp = Path(f_name) / fn
    return func_fp


def get_cache_key_old(f: callable, *args, **kwargs) -> str:
    f_name = f.__name__
    args_str = "_".join(map(str, args))
    kwargs_str = "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
    combined_str = f"{f_name}_{args_str}_{kwargs_str}"
    unique_id = hashlib.md5(combined_str.encode()).hexdigest()
    cache_key = f"{f_name}_{unique_id}"

    return cache_key


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
