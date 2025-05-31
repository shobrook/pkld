# Standard library
import hashlib
import inspect
import warnings
from pathlib import Path
from typing import Optional
from inspect import Parameter

# Third-party
from filelock import FileLock


#########
# HELPERS
#########


CACHE_DIR = ".pkljar"
GLOBAL_CACHE_DIR = None

# ANSI color codes
YELLOW = "\033[93m"
LIGHT_GRAY = "\033[37m"
BOLD = "\033[1m"
RESET = "\033[0m"


class PickleWrapWarning(UserWarning):
    pass


def process_signature(f, args):
    """
    Process function signature and arguments, handling *args parameters correctly.

    Args:
        f: The function to analyze
        args: Tuple of positional arguments passed to the function

    Returns:
        dict: Mapping of parameter names to argument values
    """
    sig = inspect.signature(f)
    arg_kwargs = {}
    args_iter = iter(args)

    # First pass: identify regular params and VAR_POSITIONAL
    for name, param in sig.parameters.items():
        if param.kind == Parameter.VAR_POSITIONAL:
            break
        elif param.kind in (Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD):
            try:
                arg_kwargs[name] = next(args_iter)
            except StopIteration:
                # No more arguments available
                break

    return arg_kwargs, args_iter


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


def get_parent_file(f: callable) -> Path:
    return Path(f.__globals__["__file__"])


def get_parent_dir(f: callable) -> Path:
    return get_parent_file(f).parent


######
# MAIN
######


def get_cache_dir(f: callable, cache_dir: Optional[str] = None) -> Path:
    fn_name = f.__name__
    fn_file = get_parent_file(f).stem
    fn_dir = get_parent_dir(f)
    cache_dir = Path(cache_dir or GLOBAL_CACHE_DIR or fn_dir / CACHE_DIR)
    cache_dir /= Path(fn_file) / Path(fn_name)

    # .../<filename_fn_belongs_to>/<fn_name>/

    return cache_dir


def get_cache_fp(
    f: callable,
    args,
    kwargs,
    cache_dir: Optional[str] = None,
    cache_fp: Optional[str] = None,
    max_fn_len: int = 128,
) -> Path:
    cache_dir = get_cache_dir(f, cache_dir)
    if cache_fp:
        return cache_dir / Path(cache_fp)

    kwargs = add_defaults_to_kwargs(f, kwargs)
    cache_key = get_args_str(args) + get_kwargs_str(kwargs)
    if len(cache_key) > max_fn_len:
        cache_key = hashlib.md5(cache_key.encode()).hexdigest()[:max_fn_len]

    cache_fp = cache_dir
    cache_fp /= Path(f"{cache_key}.pkl")

    return cache_fp


def get_file_lock(cache_fp: Path) -> FileLock:
    if cache_fp.is_dir():
        lock_fp = str(cache_fp / Path("L.lock"))
    else:
        lock_fp = str(cache_fp) + ".lock"

    lock = FileLock(lock_fp)
    return lock


def get_logger(verbose: bool = False) -> callable:
    def log(s: str):
        if verbose:
            print(f"{YELLOW}{BOLD}[pkld] {RESET}{LIGHT_GRAY}{s}{RESET}")

    return log
