# Standard library
import os
import pickle
import hashlib
from typing import Optional

YELLOW = "\033[93m"
RESET = "\033[0m"
CACHE_DIR = ".marinade"


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


def get_cache_key(f: callable, *args, **kwargs) -> str:
    f_name = f.__name__
    args_str = "_".join(map(str, args))
    kwargs_str = "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
    combined_str = f"{f_name}_{args_str}_{kwargs_str}"
    unique_id = hashlib.md5(combined_str.encode()).hexdigest()
    cache_key = f"{f_name}_{unique_id}"

    return cache_key


def get_cached_output(path: str) -> any:
    with open(path, "rb") as file:
        output = pickle.load(file)
        return output


def cache_output(output: any, path: str):
    with open(path, "wb") as file:
        pickle.dump(output, file)


def get_logger(verbose: bool = False) -> callable:
    def log(s: str):
        if verbose:
            print(f"{YELLOW}marinate | {s}{RESET}")

    return log
