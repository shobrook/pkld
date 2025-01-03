# pkld

`pkld` (pronounced "pickled") caches function calls to your disk.

This saves you from repeating the same function calls every time you run your code. It's especially useful in data engineering or machine learning pipelines, where function calls are often expensive or time-consuming.

```python
from pkld import pkld

@pkld
def foo(input):
    # Slow or expensive operations...
    return stuff
```

**Features:**

- Uses [pickle](https://docs.python.org/3/library/pickle.html) to store function outputs locally
- Supports functions with mutable or un-hashable arguments (e.g. dicts, lists, numpy arrays)
- Can also be used as an **in-memory (i.e. transient) cache**
- Supports asynchronous functions
- Thread-safe

## Installation

```bash
> pip install pkld
```

## Usage

To use, just add the `@pkld` decorator to your function:

```python
from pkld import pkld

@pkld
def foo():
    return stuff
```

Then if you run the program, the function will be executed:

```python
stuff = foo() # Takes a long time
```

And if you run it again:

```python
stuff = foo() # Fast af
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
def foo():
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
def foo():
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
def foo():
    return stuff # Output will be loaded/stored in memory
```

This is preferred if you only care about memoizing operations _within_ a single run of your program, rather than _across_ runs.

You can also enable both in-memory and on-disk caching by setting `store="both"`. Loading from a memory cache is faster than a disk cache. So by using both, you can get the speed benefits of in-memory and the persistence benefits of on-disk.

## API

**pkld()**

- `cache_fp`
- `verbose`

## Limitations

TODO: Provide examples

Only certain functions can and should be pickled:

1. Functions should not have side-effects.
2. If function arguments are mutable, they should _not_ be mutated by the function.
3. Not all methods in classes should be cached.
4. Don't pickle functions that take less than a second. The disk I/O overhead will negate the benefits of caching. You _can_ use the in-memory cache, though.
5. Functions that return an unpickleable object, e.g. sockets or database connections, cannot be cached.

<!--6. Functions _must_ be pure and deterministic. Meaning they should produce the same output given the same input, and should not have side-effects.-->

## Authors

Created by [Paul Bogdan](https://github.com/paulcbogdan) and [Jonathan Shobrook.](https://github.com/shobrook)
