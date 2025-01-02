TODO: Finish README

# pkld

`pkld` (pronounced "pickled") caches function calls to your disk.

This saves you from recomputing functions every time you run your code. It's especially useful in data processing or machine learning pipelines, where function calls are often expensive or time-consuming.

```python
from pkld import pkld

@pkld
def my_slow_fn(input):
    # Function that's slow or expensive
```

`pkld` can also serve as an in-memory (i.e. transient) cache if needed.

**Features:**

- Uses pickle to store function outputs locally
- Supports functions with mutable or un-hashable arguments (e.g. dicts, lists, numpy arrays)
- Thread-safe
- Supports asynchronous functions
- Control the cache lifetime and location

## Installation

```bash
> pip install pkld
```

## Usage

To start, just add the `@pkld` decorator to it:

```python
from pkld import pkld

@pkld
def my_fn():
    # Does something
```

If you later modify the function, you can invalidate its cache using the `overwrite` parameter:

```python
@marinate(overwrite=True)
def my_fn():
    # Does something different
```

This will force a function call and overwrite whatever's in the cache.

### Cache location

By default, cached function calls are stored in the same directory as the files they're defined in. You'll find them in a folder called `.marinade`.

However, you can change where a function call is stored by setting the `cache_dir` parameter in the decorator:

```python
@marinate(cache_dir="~/pickle_jar")
def my_fn():
    # ...
```

After running your program, you'll see pickle (`.pkl`) files appear in the directory you specified.

You can also specify a cache directory for _all_ marinated functions:

```python
from marinate import set_cache_dir

set_cache_dir("~/pickle_jar")

@marinate
def my_fn():
    # Output will be stored in ~/pickle_jar
```

### Disk vs. RAM

You can also use `marinate` to cache functions in-memory rather than on-disk. This is preferred if you only care about memoizing operations _within_ a single run of a program, rather than _across_ runs.

```python
@marinate(store="memory")
def my_fn():
    # Do things
```

In other words, `@marinate` is a drop-in replacement for Python's built-in `@cache` decorator.

## Limitations

Only certain functions can and should be marinated:

1. Functions that return an unpickleable object, e.g. sockets or database connections, cannot be cached.
2. Functions _must_ be pure and deterministic. Meaning they should produce the same output given the same input, and should not have side-effects.
3. Function arguments must be hashable.
4. Don't marinate functions that take less than a second. The disk I/O overhead will negate the benefits of caching.
5. Not all methods in classes should be cached.

- Also ignore self when generating cache key
- Make a global enable_cache and disable_cache function
- .disable and .enable methods on functions
- .picklejar instead of .marinade
- Be careful with mutable inputs.
- Be careful with side-effects.

## Authors

Created by [Paul Bogdan](https://github.com/paulcbogdan) and [Jonathan Shobrook](https://github.com/shobrook) to make our lives easier when iterating on data/training pipelines.
