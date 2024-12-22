# marinate

`marinate` caches function calls to your disk. This lets you memoize operations _across runs_ of a program. So even if your program terminates, you can run it again without re-invoking slow or expensive functions.

```python
from marinate import marinate

@marinate
def my_slow_fn(input):
    # Function that's slow or expensive
```

**Features:**

- Thread-safe
- Supports asynchronous functions
- Supports in-memory caching in addition to on-disk
- Uses Python's built-in `pickle` module under the hood

## Installation

```bash
> pip install marinate
```

## Usage

To marinate a function just add the `@marinate` decorator to it:

```python
from marinate import marinate

@marinate
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

## Authors

Created by [Paul Bogdan](https://github.com/paulcbogdan) and [Jonathan Shobrook](https://github.com/shobrook) to make our lives easier when iterating on data/training pipelines.
