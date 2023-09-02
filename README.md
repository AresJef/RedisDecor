## Provides decorators to cache/update/delete results to/from Redis.

Created to be used in a project, this package is published to github 
for ease of management and installation across different modules.

### Features
For function decorated with `@cache`, the result will be serialized and 
stored in Redis. If the function is called again with the same arguments
before the expiration, the value will be retrieved from Redis and deserialized
and reconstruct to its original (or compatible) python dtype.

Supported caching data types includes:
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

### Installation
Install from `PyPi`
``` bash
pip install redisdecor
```

Install from `github`
``` bash
pip install git+https://github.com/AresJef/RedisDecor.git
```

### Compatibility
Only support for python 3.10 and above.

### Usage (Setup)
``` python
import redisdecor as rd
import datetime, numpy as np, pandas as pd
# Decorators in this package relies on `Redis`, which is a
# subclass of `redis.StrictRedis`. Besides the arguments
# `decode_responses` is fixed to False, this subclass works
# the same as `redis.StrictRedis`.
cl = rd.get_client(host="127.0.0.1", db=10)

# A shared 'expensive' function for all three decorators
def gen_data(rows: int, offset: int = 0) -> pd.DataFrame:
    # Add some delay to simulate expensiveness
    time.sleep(1)
    # Generate a pandas DataFrame
    tz = datetime.timezone(datetime.timedelta(hours=8), "CUS")
    dt = datetime.datetime.now()
    dt = datetime.datetime(2023, 1, 1, 1, 1, 1, 1)
    val = {
        "bool": True,
        "np_bool": np.bool_(False),
        "int": 1 + offset,
        "int64": np.int64(5 + offset),
        "unit": np.uint(5 + offset),
        "unit64": np.uint64(5 + offset),
        "float": 1.1 + offset,
        "float64": np.float64(4.4 + offset),
        "decimal": Decimal("3.3"),
        "str": "STRING",
        "bytes": b"BYTES",
        "datetime": dt + datetime.timedelta(offset),
        "datetime_tz": (dt + datetime.timedelta(offset)).replace(tzinfo=tz),
        "time": (dt + datetime.timedelta(hours=offset)).time(),
        "time_tz": (dt + datetime.timedelta(hours=offset)).time().replace(tzinfo=tz),
        "timedelta": datetime.timedelta(1 + offset),
        "None": None,
    }
    return pd.DataFrame([val for _ in range(rows)])

# Shared prefix for all three decorators
prefix = "test"

# @cache decorator - returns function value
@rd.cache(cl, prefix, 60)
def gen_data_cache(rows: int) -> pd.DataFrame:
    return gen_data(rows, 0)

# @update decorator - return bool | None
@rd.update(cl, prefix)
def gen_data_update(rows: int) -> bool | None:
    return gen_data(rows, 1)

# @delete decorator return bool | None
@rd.delete(cl, prefix) 
def gen_data_delete(rows: int) -> bool | None:
    return gen_data(rows, 0)
```

### Usage (Cache)
``` python
from timeit import timeit

# Flush keys
cl.flushall()

# First call - (no cache) - corresponding key: "test:100::"
print("No. cache - 100 row".ljust(20), timeit(lambda: gen_data_cache(100), number=1))
# No. cache - 100 row  1.0088350829901174

# Second call - (cache hit) - corresponding key: "test:100::"
print("Hit cache - 100 row".ljust(20), timeit(lambda: gen_data_cache(100), number=1))
# Hit cache - 100 row  0.002061583974864334

# Call with different arguments - (no cache) - corresponding key: "test:90::"
print("No. cache - 90 row".ljust(20), timeit(lambda: gen_data_cache(90), number=1))
# No. cache - 90 row   1.0119208749965765

# Second call - (cache hit) - corresponding key: "test:90::"
print("Hit cache - 90 row".ljust(20), timeit(lambda: gen_data_cache(90), number=1))
# Hit cache - 90 row   0.001857625029515475

# Data
print(gen_data_cache(100))
# <pandas.DataFrame>
# bool np_bool int int64 unit unit64 float ... bytes datetime datetime_tz time time_tz timedelta None
# 0 True False 1 5 5 5 1.1 ... 2023-01-01 01:01:01.000001 2023-01-01 01:01:01.000001+08:00 01:01:01.000001 01:01:01.000001+08:00 1 days None
# 1 True False 1 5 5 5 1.1 ... 2023-01-01 01:01:01.000001 2023-01-01 01:01:01.000001+08:00 01:01:01.000001 01:01:01.000001+08:00 1 days None
# 2 True False 1 5 5 5 1.1 ... 2023-01-01 01:01:01.000001 2023-01-01 01:01:01.000001+08:00 01:01:01.000001 01:01:01.000001+08:00 1 days None
# 3 True False 1 5 5 5 1.1 ... 2023-01-01 01:01:01.000001 2023-01-01 01:01:01.000001+08:00 01:01:01.000001 01:01:01.000001+08:00 1 days None
# 4 True False 1 5 5 5 1.1 ... 2023-01-01 01:01:01.000001 2023-01-01 01:01:01.000001+08:00 01:01:01.000001 01:01:01.000001+08:00 1 days None
# .. ... ... ... ... ... ... ... ... ... ... ... ... ... ... ...
# 95 True False 1 5 5 5 1.1 ... 2023-01-01 01:01:01.000001 2023-01-01 01:01:01.000001+08:00 01:01:01.000001 01:01:01.000001+08:00 1 days None
# 96 True False 1 5 5 5 1.1 ... 2023-01-01 01:01:01.000001 2023-01-01 01:01:01.000001+08:00 01:01:01.000001 01:01:01.000001+08:00 1 days None
# 97 True False 1 5 5 5 1.1 ... 2023-01-01 01:01:01.000001 2023-01-01 01:01:01.000001+08:00 01:01:01.000001 01:01:01.000001+08:00 1 days None
# 98 True False 1 5 5 5 1.1 ... 2023-01-01 01:01:01.000001 2023-01-01 01:01:01.000001+08:00 01:01:01.000001 01:01:01.000001+08:00 1 days None
# 99 True False 1 5 5 5 1.1 ... 2023-01-01 01:01:01.000001 2023-01-01 01:01:01.000001+08:00 01:01:01.000001 01:01:01.000001+08:00 1 days None
# [100 rows x 17 columns]
```

### Usage (Update)
``` python
# Update existing cache - corresponding key: "test:100::"
print("Update cache - 100 row".ljust(20), timeit(lambda: gen_data_update(100), number=1))
# Update cache - 100 row 1.0083019589656033
print("Update status:", gen_data_update(100)) # Will return True since the key exists.
# Update status: True

# Update non-exist cache - corresponding key: "test:80::"
print("Update miss - 80 row".ljust(20), timeit(lambda: gen_data_update(80), number=1))
# Update miss - 80 row   0.00012520799646154046
print("Update status:", gen_data_update(80)) # Will return False since the key does not exist.
# Update status: False

# Data
print(gen_data_cache(100)) # Call cache function to retrieve the updated data
# <pandas.DataFrame>
# bool np_bool int int64 unit unit64 float ... bytes datetime datetime_tz time time_tz timedelta None
# 0 True False 2 6 6 6 2.1 ... 2023-01-02 01:01:01.000001 2023-01-02 01:01:01.000001+08:00 02:01:01.000001 02:01:01.000001+08:00 2 days None
# 1 True False 2 6 6 6 2.1 ... 2023-01-02 01:01:01.000001 2023-01-02 01:01:01.000001+08:00 02:01:01.000001 02:01:01.000001+08:00 2 days None
# 2 True False 2 6 6 6 2.1 ... 2023-01-02 01:01:01.000001 2023-01-02 01:01:01.000001+08:00 02:01:01.000001 02:01:01.000001+08:00 2 days None
# 3 True False 2 6 6 6 2.1 ... 2023-01-02 01:01:01.000001 2023-01-02 01:01:01.000001+08:00 02:01:01.000001 02:01:01.000001+08:00 2 days None
# 4 True False 2 6 6 6 2.1 ... 2023-01-02 01:01:01.000001 2023-01-02 01:01:01.000001+08:00 02:01:01.000001 02:01:01.000001+08:00 2 days None
# .. ... ... ... ... ... ... ... ... ... ... ... ... ... ... ...
# 95 True False 2 6 6 6 2.1 ... 2023-01-02 01:01:01.000001 2023-01-02 01:01:01.000001+08:00 02:01:01.000001 02:01:01.000001+08:00 2 days None
# 96 True False 2 6 6 6 2.1 ... 2023-01-02 01:01:01.000001 2023-01-02 01:01:01.000001+08:00 02:01:01.000001 02:01:01.000001+08:00 2 days None
# 97 True False 2 6 6 6 2.1 ... 2023-01-02 01:01:01.000001 2023-01-02 01:01:01.000001+08:00 02:01:01.000001 02:01:01.000001+08:00 2 days None
# 98 True False 2 6 6 6 2.1 ... 2023-01-02 01:01:01.000001 2023-01-02 01:01:01.000001+08:00 02:01:01.000001 02:01:01.000001+08:00 2 days None
# 99 True False 2 6 6 6 2.1 ... 2023-01-02 01:01:01.000001 2023-01-02 01:01:01.000001+08:00 02:01:01.000001 02:01:01.000001+08:00 2 days None
# [100 rows x 17 columns]
```

### Usage (Delete)
``` python
# Delete existing cache - corresponding key: "test:100::"
print("Delete cache - 100 row".ljust(20), timeit(lambda: gen_date_delete(100), number=1))
# Delete cache - 100 row 0.00010604201816022396
print("Delete status:", gen_date_delete(100)) # Will return True since the key exists.
# Delete status: True

# Delete non-exist cache - corresponding key: "test:80::"
print("Delete miss - 80 row".ljust(20), timeit(lambda: gen_date_delete(80), number=1))
# Delete miss - 80 row   9.779195534065366e-05
print("Delete status:", gen_date_delete(80)) # Will return False since the key does not exist.
# Delete status: False

# Check cache - corresponding key: "test:80::"
print("Check key:", cl.get("test:100::"))
# Check key: None
```

### Acknowledgements
redisdecor is based on several open-source repositories.
- [hiredis](https://github.com/redis/hiredis-py)
- [redis](https://github.com/redis/redis)
- [serializor](https://github.com/AresJef/Serializor)

