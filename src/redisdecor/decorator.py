# /usr/bin/python
# -*- coding: UTF-8 -*-
import datetime
from typing import Callable
from asyncio import iscoroutinefunction
from redisdecor.client import Redis
from redisdecor.utils import generate_key

__all__ = ["cache", "update", "delete"]


def cache(
    rd: Redis,
    prefix: str,
    ex: int | float | str | datetime.timedelta | datetime.datetime,
    ex_ms: bool = False,
    ex_rf: bool = False,
    cls: bool = False,
) -> Callable:
    """Redis cache decorator.
    (Support both synchronous and asynchronous functions.)

    This decorator caches the return value of the decorated function to redis.
    The redis key is determined by the prefix + function arguments, so it is
    important to ensure the prefix is an unique identifier for each function.

    :param rd: `<Redis>` The Redis client.
        - Must be an instance of `redisdecor.Redis`, because this decorator
          relies on the internal methods of the `Redis` class.

    :param prefix: `<str>` The unique prefix for the decorated function.

    :param ex: The expiry, accepts:
        - If `<int>` / `<float>` / `<str>`, the key will expire after the
          given number of seconds. (Float values will be rounded to integers.)
        - If `<datetime.timedelta>`, the key will expire after the given
          number of seconds. (Does not affected by the `ex_ms` argument.)
        - If `<datetime.datetime>`, the key will expire at the given datetime.
          (Does not affected by the `ex_ms` argument.)

    :param ex_ms: `<bool>` Whether the expiry is in milliseconds.
        - If `False` (default), the expiry is in seconds.
        - If `True`, the expiry is in milliseconds.
        - Only takes effect when `ex` is `<int>` / `<float>` / `<str>`.

    :param ex_rf: `<bool>` Whether to refresh the key's expiry when hitted.
        - If `False` (default), the key's expiry will not be updated by the
          'ex' and 'ex_ms' arguments when the key is hitted.
        - If `True`, if the key is hitted, along with returning the cached
          value, the key's expiry will be re-updated by the 'ex' and 'ex_ms'
          arguments. For example, if 'ex=60' and the decorated function is
          called before the key expires, the key's expiry will be updated to
          60 seconds when the key is hitted.

    :param cls: `<bool>` Whether the decorated function is a class method.
        - The decorator relies on the function's arguments to generate
          the redis key, and the first argument of a class method is always the
          the class instance itself. Setting this argument to `True` will remove
          the first function argument (self) when generating the redis key.

    ### Caching logic
    - 1. Generate redis key from prefix and function arguments.
    - 2. Try to get the key's cache from redis. (If `ex_rf=True`, also update the
         key's expiry if exists.)
    - 3. If cache exists, deserialize and reconstruct the cache to its original
         (or compatible) python dtype and return. For supported dtypes see
         `Supported data types` section below.
    - 4. If cache does not exists, execute the decorated function and serialize
         the return value to `bytes`. After setting the cache to redis, return
         the function's return value.
    - Notice1: If the decorated function returns `None`, the value will not be
         cached to redis. This behavior helps to avoid ambiguity between a key
         that does not exists and a key that exists but its value is `None`.
         Also, it allows the decorated function to implement its own logic to
         skip caching (by returning `None`).
    - Notice2: The returned value of the decorated function might be 'different'
         between cache hit and cache miss. If cache is missed, the function's
         return value will be returned directly (after setting the cache to redis).
         However, if cache is hitted, the return value is based on the deserialized
         and reconstructed cached value (this process might change the value's data type).
         For example, if the decorated function returns a `pandas.Timestamp` object,
         the first time the function is called (cache missed), the return value will
         be a `pandas.Timestamp` object. However, if the function is called again
         before the key expires (cache hitted), the return value will be a
         `datetime.datetime` object. For supported dtypes see `Supported data types`
         section below.

    ### Supported data types
    - boolean: `bool` & `numpy.bool_` -> deserialize to `bool`
    - integer: `int` & `numpy.int` & `numpy.uint` -> deserialize to `int`
    - float: `float` & `numpy.float_` -> deserialize to `float`
    - decimal: `decimal.Decimal` -> deserialize to `decimal.Decimal`
    - string: `str` -> deserialize to `str`
    - bytes: `bytes` -> deserialize to `bytes`
    - date: `datetime.date` -> deserialize to `datetime.date`
    - time: `datetime.time` -> deserialize to `datetime.time`
    - datetime: `datetime.datetime` & `pandas.Timestamp` -> deserialize to `datetime.datetime`
    - datetime64*: `numpy.datetime64` & `time.struct_time` -> deserialize to `datetime.datetime`
    - timedelta: `datetime.timedelta` & `pandas.Timedelta` -> deserialize to `datetime.timedelta`
    - timedelta64: `numpy.timedelta64` -> deserialize to `datetime.timedelta`
    - None: `None` & `numpy.nan` -> deserialize to `None`
    - list: `list` of above supported data types -> deserialize to `list`
    - tuple: `tuple` of above supported data types -> deserialize to `list`
    - set: `set` of above supported data types -> deserialize to `list`
    - frozenset: `frozenset` of above supported data types -> deserialize to `list`
    - dict: `dict` of above supported data types -> deserialize to `dict`
    - numpy.record: `numpy.record` of above supported data types -> deserialize to `list`
    - numpy.ndarray: `numpy.ndarray` of above supported data types -> deserialize to `np.ndarray`
    - pandas.Series: `pandas.Series` of above supported data types -> deserialize to `pandas.Series`
    - pandas.DataFrame: `pandas.DataFrame` of above supported data types -> deserialize to `pandas.DataFrame`

    ### Error handling
    - This decorator is designed to be a silent decorator, which means it will
      not raise any error (redis side). Instead, it only issues a warning message
      when a redis error occurs and the function will just be executed and returned
      normally.
    - Error from the decorated function itself will still be raised as normal.
    """

    def decorator(func: Callable) -> Callable:
        def sync_wrapper(*args, **kwargs) -> object:
            # Generate key
            key: str = generate_key(prefix, args, kwargs)
            # Get cache from redis
            cch = rd.decor_cache_get(key, ex, ex_ms, ex_rf)
            # Cache miss
            if cch is None:
                res = func(*args, **kwargs)  # . execute function
                if res is not None:
                    rd.decor_cache_set(key, res, ex, ex_ms)  # . set cache
                return res
            # Cache hit
            else:
                return cch

        async def async_wrapper(*args, **kwargs) -> object:
            # Generate key
            key: str = generate_key(prefix, args, kwargs)
            # Get cache from redis
            cch = rd.decor_cache_get(key, ex, ex_ms, ex_rf)
            # Cache miss
            if cch is None:
                res = await func(*args, **kwargs)  # . execute function
                if res is not None:
                    rd.decor_cache_set(key, res, ex, ex_ms)  # . set cache
                return res
            # Cache hit
            else:
                return cch

        def cls_sync_wrapper(self, *args, **kwargs) -> object:
            # Generate key
            key: str = generate_key(prefix, args, kwargs)
            # Get cache from redis
            cch = rd.decor_cache_get(key, ex, ex_ms, ex_rf)
            # Cache miss
            if cch is None:
                res = func(self, *args, **kwargs)  # . execute function
                if res is not None:
                    rd.decor_cache_set(key, res, ex, ex_ms)  # . set cache
                return res
            # Cache hit
            else:
                return cch

        async def cls_async_wrapper(self, *args, **kwargs) -> object:
            # Generate key
            key: str = generate_key(prefix, args, kwargs)
            # Get cache from redis
            cch = rd.decor_cache_get(key, ex, ex_ms, ex_rf)
            # Cache miss
            if cch is None:
                res = await func(self, *args, **kwargs)  # . execute function
                if res is not None:
                    rd.decor_cache_set(key, res, ex, ex_ms)  # . set cache
                return res
            # Cache hit
            else:
                return cch

        # Determine wrapper
        if cls:
            if iscoroutinefunction(func):
                return cls_async_wrapper
            else:
                return cls_sync_wrapper
        else:
            if iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

    # Return decorator
    return decorator


def update(rd: Redis, prefix: str, cls: bool = False) -> Callable:
    """Redis update decorator.
    (Support both synchronous and asynchronous functions.)

    This decorator updates the cache (key) values in redis from the decorated
    function. The redis key is determined by the prefix + function arguments,
    and should match identically with the `cache` decorator's prefix + function
    arguments (For more detail, see `Exmaple` section below).

    :param rd: `<Redis>` The Redis client.
        - Must be an instance of `redisdecor.Redis`, because this decorator
          relies on the internal methods of the `Redis` class.

    :param prefix: `<str>` The unique prefix for the decorated function.

    :param cls: `<bool>` Whether the decorated function is a class method.
        - The decorator relies on the function's arguments to generate
          the redis key, and the first argument of a class method is always the
          the class instance itself. Setting this argument to `True` will remove
          the first function argument (self) when generating the redis key.

    :return: `<bool>` Whether the key has been updated.
        - It is `IMPORTANT` to notice that, function decorated with `update`
          will not return the function's value. Instead, it will return `True`
          if the key has been updated, or `False` if update is skipped.
          `None` will be returned if any redis error occurs.

    ### Update logic
    - 1. Generate redis key from prefix and function arguments.
    - 2. Check if the key exists in redis.
    - 3. If key exists, execute the decorated function, serialize the value and update
         the redis key. The expiry (ttl) of the key will be retained. Lastly, return
        `True` to indicate the key has been updated.
    - 4. If key does not exists, do nothing and return `False` to indicate update
         has been skipped.
    - Notice: If the decorated function returns `None`, the value will not be
         updated to redis. This behavior helps to avoid ambiguity between a key
         that does not exists and a key that exists but its value is `None`.
         Also, it allows the decorated function to implement its own logic to
         skip cache/update (by returning `None`).

    ### Supported data types
    Please refer to the `cache` decorator's `Supported data types` section.

    ### Error handling
    - This decorator is designed to be a silent decorator, which means it will
      not raise any error (redis side). Instead, it only issues a warning message
      when a redis error occurs and returns `None` at the end.
    - Error from the decorated function itself will still be raised as normal.

    ### Exmaple (Use alongside with `cache` decorator)
    >>> import redisdecor as rd
        cl = rd.get_client(host="127.0.0.1")

    >>> # Function decorated with `cache`
        @rd.cache("myfunc", 10, False, False, False)
        def expensive_func_cache(x, y):
            return ...

    >>> # Function decorated with `update`
        @rd.update("myfunc", False)
        def expensive_func_update(x, y):
            return ...

    In this exmaple, both `expensive_func_cache` and `expensive_func_update` uses the
    same 'prefix' for cache/update decorators and takes the same arguments (x, y) as input.
    Therefore, when calling `expensive_func_update(1, 1)`, the redis cache setted by
    `expensive_func_cache(1, 1)` will be updated by function `expensive_func_update`'s
    return value (if the redis key "myfunc:1:1::" still exists).
    """

    def decorator(func: Callable) -> Callable:
        def sync_wrapper(*args, **kwargs) -> bool | None:
            # Generate key
            key: str = generate_key(prefix, args, kwargs)
            # Cache exists - update
            if rd.decor_update_exists(key):
                res = func(*args, **kwargs)
                if res is not None:
                    return rd.decor_update_set(key, res)
            return False

        async def async_wrapper(*args, **kwargs) -> bool | None:
            # Generate key
            key: str = generate_key(prefix, args, kwargs)
            # Cache exists - update
            if rd.decor_update_exists(key):
                res = await func(*args, **kwargs)
                if res is not None:
                    return rd.decor_update_set(key, res)
            return False

        def cls_sync_wrapper(self, *args, **kwargs) -> bool | None:
            # Generate key
            key: str = generate_key(prefix, args, kwargs)
            # Cache exists - update
            if rd.decor_update_exists(key):
                res = func(self, *args, **kwargs)
                if res is not None:
                    return rd.decor_update_set(key, res)
            return False

        async def cls_async_wrapper(self, *args, **kwargs) -> bool | None:
            # Generate key
            key: str = generate_key(prefix, args, kwargs)
            # Cache exists - update
            if rd.decor_update_exists(key):
                res = await func(self, *args, **kwargs)
                if res is not None:
                    return rd.decor_update_set(key, res)
            return False

        # Determine wrapper
        if cls:
            if iscoroutinefunction(func):
                return cls_async_wrapper
            else:
                return cls_sync_wrapper
        else:
            if iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

    # Return decorator
    return decorator


def delete(rd: Redis, prefix: str, cls: bool = False) -> Callable:
    """Redis delete decorator.
    (Support both synchronous and asynchronous functions.)

    This decorator deletes the cache (key) in redis from the decorated
    function. The redis key is determined by the prefix + function arguments,
    and should match identically with the `cache` decorator's prefix + function
    arguments (For more detail, see `Exmaple` section below).

    :param rd: `<Redis>` The Redis client.
        - Must be an instance of `redisdecor.Redis`, because this decorator
          relies on the internal methods of the `Redis` class.

    :param prefix: `<str>` The unique prefix for the decorated function.

    :param cls: `<bool>` Whether the decorated function is a class method.
        - The decorator relies on the function's arguments to generate
          the redis key, and the first argument of a class method is always the
          the class instance itself. Setting this argument to `True` will remove
          the first function argument (self) when generating the redis key.

    :return: `<bool>` Whether the key has been deleted.
        - It is `IMPORTANT` to notice that, function decorated with `delete`
          will not return the function's value. Instead, it will return `True`
          if the key has been deleted, or `False` if key does not exists.
          `None` will be returned if any redis error occurs.

    ### Delete logic
    - 1. Generate redis key from prefix and function arguments.
    - 2. Delete the key from redis.
    - 3. Return `True` to indicate the key has been deleted, or `False` if key
         does not exists.
    - Notice: function decorated with `delete` will not be executed in any cases.
         Instead, only the function arguments are used to generate the redis key
         to be deleted.

    ### Error handling
    - This decorator is designed to be a silent decorator, which means it will
      not raise any error (redis side). Instead, it only issues a warning message
      when a redis error occurs and returns `None` at the end.

    ### Exmaple (Use alongside with `cache` decorator)
    >>> import redisdecor as rd
        cl = rd.get_client(host="127.0.0.1")

    >>> # Function decorated with `cache`
        @rd.cache("myfunc", 10, False, False, False)
        def expensive_func_cache(x, y):
            return ...

    >>> # Function decorated with `delete`
        @rd.delete("myfunc", False)
        def expensive_func_delete(x, y):
            return ...

    In this exmaple, both `expensive_func_cache` and `expensive_func_delete` uses the
    same 'prefix' for cache/delete decorators and takes the same arguments (x, y) as input.
    Therefore, when calling `expensive_func_delete(1, 1)`, the redis cache setted by
    `expensive_func_cache(1, 1)` will be deleted (if the redis key "myfunc:1:1::" exists).
    """

    def decorator(func: Callable) -> Callable:
        def sync_wrapper(*args, **kwargs) -> bool | None:
            # Generate key
            key: str = generate_key(prefix, args, kwargs)
            # Delete cache
            return rd.decor_delete(key)

        async def async_wrapper(*args, **kwargs) -> bool | None:
            # Generate key
            key: str = generate_key(prefix, args, kwargs)
            # Delete cache
            return rd.decor_delete(key)

        def cls_sync_wrapper(_, *args, **kwargs) -> bool | None:
            # Generate key
            key: str = generate_key(prefix, args, kwargs)
            # Delete cache
            return rd.decor_delete(key)

        async def cls_async_wrapper(_, *args, **kwargs) -> bool | None:
            # Generate key
            key: str = generate_key(prefix, args, kwargs)
            # Delete cache
            return rd.decor_delete(key)

        # Determine wrapper
        if cls:
            if iscoroutinefunction(func):
                return cls_async_wrapper
            else:
                return cls_sync_wrapper
        else:
            if iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

    # Return decorator
    return decorator
