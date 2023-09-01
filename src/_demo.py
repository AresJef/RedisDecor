# /usr/bin/python
# -*- coding: UTF-8 -*-
import time
from timeit import timeit
from decimal import Decimal
import datetime, numpy as np, pandas as pd


def demo() -> None:
    import redisdecor as rd

    cl = rd.get_client(host="127.0.0.1", db=10)

    # Some expensive function
    def gen_data(rows: int = 1, offset: int = 0) -> pd.DataFrame:
        tz = datetime.timezone(datetime.timedelta(hours=8), "CUS")
        dt = datetime.datetime.now()
        dt = datetime.datetime(2023, 1, 1, 1, 1, 1, 1)
        # fmt: off
        val = {
            "bool": True,
            "np_bool": np.bool_(False),
            "int": 1 + offset,
            "int8": np.int8(2 + offset),
            "int16": np.int16(3 + offset),
            "int32": np.int32(4 + offset),
            "int64": np.int64(5 + offset),
            "unit": np.uint(5 + offset),
            "unit16": np.uint16(5 + offset),
            "unit32": np.uint32(5 + offset),
            "unit64": np.uint64(5 + offset),
            "float": 1.1 + offset,
            "float16": np.float16(2.2 + offset),
            "float32": np.float32(3.3 + offset),
            "float64": np.float64(4.4 + offset),
            "decimal": Decimal("3.3"),
            "str": "STRING",
            "bytes": b"BYTES",
            "datetime": dt + datetime.timedelta(offset),
            "datetime_tz": (dt + datetime.timedelta(offset)).replace(tzinfo=tz),
            "Timestamp": pd.Timestamp(dt + datetime.timedelta(offset)),
            "Timestamp_tz": (pd.Timestamp(dt + datetime.timedelta(offset))).replace(tzinfo=tz),
            "time": (dt + datetime.timedelta(hours=offset)).time(),
            "time_tz": (dt + datetime.timedelta(hours=offset)).time().replace(tzinfo=tz),
            "timedelta": datetime.timedelta(1 + offset),
            "Timedelta": pd.Timedelta(1 + offset, "D"),
            "datetime64": np.datetime64(dt + datetime.timedelta(offset)),
            "timedelta64": np.timedelta64(2 + offset, "D"),
            "None": None,
        }
        time.sleep(1)
        # fmt: on
        return pd.DataFrame([val for _ in range(rows)])

    prefix = "demo"  # prefix for the function
    ex = 60  # expire time in seconds

    # Cache decorator
    @rd.cache(cl, prefix, ex)
    def gen_data_cache(rows: int = 1) -> list[dict]:
        return gen_data(rows, 0)

    @rd.update(cl, prefix)
    def gen_data_update(rows: int = 1) -> list[dict]:
        return gen_data(rows, 1)

    @rd.delete(cl, prefix)
    def gen_date_delete(rows: int = 1) -> None:
        return gen_data(rows, 0)

    # fmt: off
    # Test cache
    cl.flushall()

    # First call - (no cache)
    print("No. cache - 100 row".ljust(20), timeit(lambda: gen_data_cache(100), number=1))

    # Second call - (cache hit)
    print("Hit cache - 100 row".ljust(20), timeit(lambda: gen_data_cache(100), number=1))

    # Call with different arguments - (no cache)
    print("No. cache - 90 row".ljust(20), timeit(lambda: gen_data_cache(90), number=1))

    # Second call - (cache hit)
    print("Hit cache - 90 row".ljust(20), timeit(lambda: gen_data_cache(90), number=1))

    # Update existing cache
    print("Update cache - 100 row".ljust(20), timeit(lambda: gen_data_update(100), number=1))
    print("Update status:", gen_data_update(100))

    # Update non-exist cache
    print("Update miss - 80 row".ljust(20), timeit(lambda: gen_data_update(80), number=1))
    print("Update status:", gen_data_update(80))

    # Delete existing cache
    print("Delete cache - 100 row".ljust(20), timeit(lambda: gen_date_delete(100), number=1))
    print("Delete status:", gen_date_delete(100))

    # Delete non-exist cache
    print("Delete miss - 80 row".ljust(20), timeit(lambda: gen_date_delete(80), number=1))
    print("Delete status:", gen_date_delete(80))

    # Check cache
    print("Check key:", cl.get("demo:100::"))
    # fmt: on


if __name__ == "__main__":
    demo()
