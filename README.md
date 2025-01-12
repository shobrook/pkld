# pkld

`pkld` (pickled) caches function calls to your disk. 

This saves you from re-executing the same function calls every time you run your code. It's especially useful in data analysis or machine learning pipelines where function calls are usually expensive or time-consuming.

```python
from pkld import pkld

@pkld
def foo(input):
    # Slow or expensive operations...
    return stuff
```

## Highlights

- Easy to use, it's just a function decorator
- Uses [pickle](https://docs.python.org/3/library/pickle.html) to store function outputs locally
- Can also be used as an in-memory (i.e. transient) cache
- Supports functions with mutable or un-hashable arguments (dicts, lists, numpy arrays)
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

The first time you run the program, the `pkld` function will be executed and the output will be saved:

```python
stuff = foo(123) # Takes a long time
```

And if you run it again (within the same Python session or a new one):

```python
stuff = foo(123) # Now fast
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

`pkld(cache_fp=None, cache_dir=None, disabled=False, store="disk", verbose=False)`

- `cache_fp: str`: File where the cached results will be stored; overrides the automatically generated filepath.
- `cache_dir: str`: Directory where the cached results will be stored; overrides the automatically generated directory.
- `disabled: bool`: If set to `True`, caching is disabled and the function will execute normally without storing or loading results.
- `store: "disk" | "memory" | "both"`: Determines the caching method. "disk" for on-disk caching, "memory" for in-memory caching, and "both" for using both methods.
- `verbose: bool`: If set to `True`, enables logging of cache operations for debugging purposes.


## Limitations

There are some contexts where you may not want to use `pkld`:

1. Only returned values are cached and any of a function's side-effects will not be captured
2. You should not use this for functions that cannot return an unpickleable object, e.g. a socket or database connection
3. If you are passing an instance of user-defined class as a function input, a `__hash__` method should be defined to avoid filepath collisions

## Authors

Created by [Paul Bogdan](https://github.com/paulcbogdan) and [Jonathan Shobrook.](https://github.com/shobrook)
