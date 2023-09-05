# /usr/bin/python
# -*- coding: UTF-8 -*-
def demo() -> None:
    import time
    from timeit import timeit
    from decimal import Decimal
    import datetime, numpy as np, pandas as pd
    import redisdecor as rd

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
            "time_tz": (dt + datetime.timedelta(hours=offset))
            .time()
            .replace(tzinfo=tz),
            "timedelta": datetime.timedelta(1 + offset),
            "None": None,
        }
        return pd.DataFrame([val for _ in range(rows)])

    # Shared prefix for all three decorators
    prefix = "test"

    # @cache decorator
    @rd.cache(cl, prefix, 60)
    def gen_data_cache(rows: int) -> pd.DataFrame:
        return gen_data(rows, 0)

    # @update decorator
    @rd.update(cl, prefix)
    def gen_data_update(rows: int) -> bool | None:
        return gen_data(rows, 1)

    # @delete decorator
    @rd.delete(cl, prefix)
    def gen_data_delete(rows: int) -> bool | None:
        return gen_data(rows, 0)

    # fmt: off
    # Test cache
    cl.flushall()

    # First call - (no cache)
    print("No. cache - 100 row".ljust(20), timeit(lambda: gen_data_cache(100), number=1))

    # Second call - (cache hit)
    print("Hit cache - 100 row".ljust(20), timeit(lambda: gen_data_cache(100), number=1))

    # Print cache
    print("Print cache:")
    print(gen_data_cache(100))

    # Call with different arguments - (no cache)
    print("No. cache - 90 row".ljust(20), timeit(lambda: gen_data_cache(90), number=1))

    # Second call - (cache hit)
    print("Hit cache - 90 row".ljust(20), timeit(lambda: gen_data_cache(90), number=1))

    # Update existing cache
    print("Update cache - 100 row".ljust(20), timeit(lambda: gen_data_update(100), number=1))
    print("Update status:", gen_data_update(100))

    # Print cache
    print("Print cache:")
    print(gen_data_cache(100))

    # Update non-exist cache
    print("Update miss - 80 row".ljust(20), timeit(lambda: gen_data_update(80), number=1))
    print("Update status:", gen_data_update(80))

    # Delete existing cache
    print("Delete cache - 100 row".ljust(20), timeit(lambda: gen_data_delete(100), number=1))
    print("Delete status:", gen_data_delete(100))

    # Delete non-exist cache
    print("Delete miss - 80 row".ljust(20), timeit(lambda: gen_data_delete(80), number=1))
    print("Delete status:", gen_data_delete(80))

    # Check cache
    print("Check key:", cl.get("demo:100::"))
    # fmt: on


if __name__ == "__main__":
    demo()
