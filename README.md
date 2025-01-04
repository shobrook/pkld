# pkld

`pkld` (pickled) caches function calls to your disk.

This saves you from re-executing the same function calls every time you run your code. It's especially useful in data engineering or machine learning pipelines, where function calls are usually expensive or time-consuming.

```python
from pkld import pkld

@pkld
def foo(input):
    # Slow or expensive operations...
    return stuff
```

## Highlights

- Super easy to use, it's just a function decorator
- Uses [pickle](https://docs.python.org/3/library/pickle.html) to store function outputs locally
- Can also be used as an in-memory (i.e. transient) cache
- Supports functions with mutable or un-hashable arguments (e.g. dicts, lists, numpy arrays)
- Supports asynchronous functions
- Thread-safe

## Installation

```bash
> pip install pkld
```

## Usage

To use, just add the `@pkld` decorator to the function you want to cache:

```python
from pkld import pkld

@pkld
def foo(input):
    return stuff
```

Then if you run the program, the function will be executed:

```python
stuff = foo(123) # Takes a long time
```

And if you run it again:

```python
stuff = foo(123) # Fast af
```

The function will _not_ execute, and instead the output will be pulled from the cache.

### Clearing the cache

Every pickled function has a `clear` method attached to it. You can use it to reset the cache:

```python
foo.clear()
```

### Disabling the cache

You can disable caching for a pickled function using the `disabled` parameter:

```python
@pkld(disabled=True)
def foo(input):
    return stuff
```

This will execute the function as if it wasn't decorated, which is useful if you modify the function and need to invalidate the cache.

### Changing cache location

By default, pickled function outputs are stored in the same directory as the files the functions are defined in. You'll find them in a folder called `.pkljar`.

```
codebase/
│
├── my_file.py # foo is defined in here
│
└── .pkljar/
    ├── foo_cd7648e2.pkl # foo w/ one set of args
    └── foo_95ad612b.pkl # foo w/ a different set of args
```

However, you can change this by setting the `cache_dir` parameter:

```python
@pkld(cache_dir="~/my_cache_dir")
def foo(input):
    return stuff
```

You can also specify a cache directory for _all_ pickled functions:

```python
from pkld import set_cache_dir

set_cache_dir("~/my_cache_dir")
```

### Using the memory cache

`pkld` caches results to disk by default. But you can also use it as an in-memory cache:

```python
@pkld(store="memory")
def foo(input):
    return stuff # Output will be loaded/stored in memory
```

This is preferred if you only care about memoizing operations _within_ a single run of your program, rather than _across_ runs.

You can also enable both in-memory and on-disk caching by setting `store="both"`. Loading from a memory cache is faster than a disk cache. So by using both, you can get the speed benefits of in-memory and the persistence benefits of on-disk.

## Arguments

`pkld(cache_fp=None, cache_dir=None, disabled=False, store="disk", verbose=False, branch_factor=0)`

- `cache_fp: str`: File where the cached results will be stored.
- `cache_dir: str`: Directory where the cached results will be stored.
- `disabled: bool`: If set to `True`, caching is disabled and the function will execute normally without storing or loading results.
- `store: "disk" | "memory" | "both"`: Determines the caching method. "disk" for on-disk caching, "memory" for in-memory caching, and "both" for using both methods.
- `verbose: bool`: If set to `True`, enables logging of cache operations for debugging purposes.
- `branch_factor: int`: # of subdirectories to group pickle files together in. Useful for functions that are called many times with many different parameters. If a cache directory has too many pickle files in it, you will see performance degradations.

## Limitations

Not all functions can and should be pickled. The requirements are:

1. Functions cannot have side-effects. This means they cannot mutate objects defined outside of the function (including its arguments).
2. Functions cannot return an unpickleable object, e.g. a socket or database connection.
3. Functions must be deterministic. Meaning they should _always_ produce the same output given the same input.
4. If you're passing an instance of a user-defined class as a function input, it must have a `__hash__` method defined on it.

## Authors

Created by [Paul Bogdan](https://github.com/paulcbogdan) and [Jonathan Shobrook.](https://github.com/shobrook)
