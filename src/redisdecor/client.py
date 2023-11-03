# /usr/bin/python
# -*- coding: UTF-8 -*-
from __future__ import annotations
from typing import Callable, Iterator, Literal, Any

import datetime
from redis.retry import Retry
from redis import StrictRedis, ConnectionPool
from redis.credentials import CredentialProvider
from redisdecor.logs import logger
from redisdecor.utils import serialize, deserialize
from redisdecor.utils import serialize_cond, deserialize_cond
from redisdecor.utils import timestamp_to_datetime, generate_key
from redisdecor.utils import parse_ex, parse_expire_ex, handle_exc

__all__ = ["Redis", "get_client"]


# Redis Subclass
class Redis(StrictRedis):
    """Represents a custom redis database. Subclass of `reids.StricRedis`."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        retry_on_timeout: bool = False,
        retry_on_error: list[Exception] | None = None,
        retry: Retry | None = None,
        encoding: str = "utf-8",
        encoding_errors: Literal["strict", "ignore", "replace"] = "strict",
        username: str | None = None,
        password: str | None = None,
        connection_pool: ConnectionPool | None = None,
        max_connections: int | None = None,
        single_connection_client: bool = False,
        socket_timeout: int | float | None = None,
        socket_connect_timeout: int | float | None = None,
        socket_keepalive: bool | None = None,
        socket_keepalive_options: dict[str, float] | None = None,
        unix_socket_path: str | None = None,
        ssl: bool = False,
        ssl_keyfile: str | None = None,
        ssl_password: str | None = None,
        ssl_cert_reqs: Literal["none", "optional", "required"] = "required",
        ssl_certfile: str | None = None,
        ssl_ca_certs: str | None = None,
        ssl_ca_path: str | None = None,
        ssl_ca_data: str | bytes | None = None,
        ssl_check_hostname: bool = False,
        ssl_validate_ocsp: bool = False,
        ssl_validate_ocsp_stapled: bool = False,
        ssl_ocsp_context: object | None = None,
        ssl_ocsp_expected_cert: str | None = None,
        health_check_interval: int | float = 0,
        client_name: str | None = None,
        redis_connect_func: Callable | None = None,
        credential_provider: CredentialProvider | None = None,
        protocol: int | None = 2,
    ) -> None:
        """Custom redis database. Subclass of `reids.StricRedis`.

        Decorators in this package requires this subclass to work. Besides
        fixed `decode_responses=False`, this subclass works the same as the
        `redis.StrictRedis`.

        ### Added methods
        - For decorators: generate_key, serialize, deserialize, decor_cache_get
          decor_cache_set, decor_update_exists, decor_update_set, decor_delete
        - Methods start with `x_` are custom methods with some extra features.

        ### Arguments
        :param host: `<str>` The host of the Redis server.
        :param port: `<int>` The port of the Redis server.
        :param db: `<int>` The database to use.
        :param retry_on_timeout: `<bool>` Whether to retry on timeout.
        :param retry_on_error: `<list[Exception]>` The list of exceptions to retry on.
        :param retry: `<Retry>` The custom retry policy based on `redis.Retry` object.
        :param encoding: `<str>` The default encoding to use for strings.
        :param encoding_errors: `<str>` The default error handling behavior for encoding.
        :param username: `<str>` The username to use for authentication.
        :param password: `<str>` The password to use for authentication.
        :param unix_socket_path: `<str>` The unix socket path to use for connection.
        :param socket_timeout: `<int>` The socket timeout to use for connection.
        :param socket_connect_timeout: `<int>` The socket connect timeout to use for connection.
        :param socket_keepalive: `<bool>` Whether to keepalive the socket.
        :param socket_keepalive_options: `<dict[str, float]>` The socket keepalive options.
        :param connection_pool: `<ConnectionPool>` An existing connection pool to use.
        :param max_connections: `<int>` The maximum number of connections to keep in a connection pool.
        :param single_connection_client: `<bool>` If `True`, connection pool is not used and `Redis` instance use is not thread safe.
        :param ssl: `<bool>` If `True`, use SSL for the connection.
        :param ssl_keyfile: `<str>` Path to an ssl private key.
        :param ssl_password: `<str>` Password for unlocking an encrypted private key.
        :param ssl_cert_reqs: `<str>` The SSLContext.verify_mode (none, optional, required).
        :param ssl_certfile:`<str>` Path to an ssl certificate.
        :param ssl_ca_certs: `<str>` The path to a file of concatenated CA certificates in PEM format.
        :param ssl_ca_path: `<str>` The path to a directory containing several CA certificates in PEM format.
        :param ssl_ca_data: `<str>/<bytes>` An ASCII string of one or more PEM-encoded certificates or a bytes-like object of DER-encoded certificates.
        :param ssl_check_hostname: `<bool`> If `True`, match the hostname during the SSL handshake.
        :param ssl_validate_ocsp: `<bool`> If `True`, perform a full ocsp validation (i.e not a stapled verification)
        :param ssl_validate_ocsp_stapled: `<bool`> If `True`, perform a validation on a stapled ocsp response
        :param ssl_ocsp_context: `<Context`> A fully initialized OpenSSL.SSL.Context object to be used in verifying the ssl_ocsp_expected_cert
        :param ssl_ocsp_expected_cert: `<str>` A PEM armoured string containing the expected certificate to be returned from the ocsp verification service.
        :param health_check_interval: `<float>` The number of seconds between connection health checks.
        :param client_name: `<str>` The client name to use for connection.
        :param redis_connect_func: `<Callable>` The custom function to use for connecting to Redis.
        :param credential_provider: `<CredentialProvider>` The credential provider to use for authentication. Can not be used along with username/password.
        :param protocol: `<int>` The protocol version to use, accepts: 2, 3.
        """
        super().__init__(
            host=host,
            port=port,
            db=db,
            password=password,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
            socket_keepalive=socket_keepalive,
            socket_keepalive_options=socket_keepalive_options,
            connection_pool=connection_pool,
            unix_socket_path=unix_socket_path,
            encoding=encoding,
            encoding_errors=encoding_errors,
            decode_responses=False,
            retry_on_timeout=retry_on_timeout,
            retry_on_error=retry_on_error,
            ssl=ssl,
            ssl_keyfile=ssl_keyfile,
            ssl_certfile=ssl_certfile,
            ssl_cert_reqs=ssl_cert_reqs,
            ssl_ca_certs=ssl_ca_certs,
            ssl_ca_path=ssl_ca_path,
            ssl_ca_data=ssl_ca_data,
            ssl_check_hostname=ssl_check_hostname,
            ssl_password=ssl_password,
            ssl_validate_ocsp=ssl_validate_ocsp,
            ssl_validate_ocsp_stapled=ssl_validate_ocsp_stapled,
            ssl_ocsp_context=ssl_ocsp_context,
            ssl_ocsp_expected_cert=ssl_ocsp_expected_cert,
            max_connections=max_connections,
            single_connection_client=single_connection_client,
            health_check_interval=health_check_interval,
            client_name=client_name,
            username=username,
            retry=retry,
            redis_connect_func=redis_connect_func,
            credential_provider=credential_provider,
            protocol=protocol,
        )

    # Get commands
    def x_get(
        self,
        key: str,
        deserialize: bool = True,
        raise_error: bool = True,
    ) -> bytes | Any | None:
        """Get the value at the key from Redis.

        :param key: `<str>` The redis key to get.
        :param deserialize: `<bool>` Whether to deserialize the value to its original (or compatiable) python dtype.
            - If `True` (default), thie method will try to deserialize and reconstruct
              the value to its original (or compatiable) python dtype. `NOTICE`: the key
              must be set by `x_set()` or `x_setget()` method with `serialize=True`.
            - If `False`, this method works the same as the native `get` method.
              and returns the value in `bytes` or `None`.

        :param raise_error: `<bool>` Whether to raise errors if the operation failed.
            - If `True` (default), raise errors.
            - If `False`, log the error as warrning and return `None`.

        :return: The value of the key, or `None` if the key does not exist.
        """
        try:
            return deserialize_cond(self.execute_command("GET", key), deserialize)
        except Exception as err:
            return handle_exc(err, "x_get", raise_error)

    def x_getdel(
        self,
        key: str,
        deserialize: bool = True,
        raise_error: bool = True,
    ) -> bytes | Any | None:
        """Get the value at the key and delete the key from Redis.

        :param key: `<str>` The redis key to get.
        :param deserialize: `<bool>` Whether to deserialize the value to its original (or compatiable) python dtype.
            - If `True` (default), thie method will try to deserialize and reconstruct
              the value to its original (or compatiable) python dtype. `NOTICE`: the key
              must be set by `x_set()` or `x_setget()` method with `serialize=True`.
            - If `False`, this method works the same as the native `get` method.
              and returns the value in `bytes` or `None`.

        :param raise_error: `<bool>` Whether to raise errors if the operation failed.
            - If `True` (default), raise errors.
            - If `False`, log the error as warrning and return `None`.

        :return: The value of the key, or `None` if the key does not exist.
        """
        try:
            return deserialize_cond(self.execute_command("GETDEL", key), deserialize)
        except Exception as err:
            return handle_exc(err, "x_getdel", raise_error)

    def x_getex(
        self,
        key: str,
        ex: int | str | float | datetime.timedelta | datetime.datetime | None,
        ex_ms: bool = False,
        deserialize: bool = True,
        raise_error: bool = True,
    ) -> bytes | Any | None:
        """Get the value and set the expiry of the key in Redis.

        :param ex: The expiry, accepts:
            - If `None` (default), the key will be persistent.
            - If `<int>` / `<float>` / `<str>`, the key will expire after the given number of seconds.
              (Float values will be rounded to integers.)
            - If `<datetime.timedelta>`, the key will expire after the given number of seconds.
              (Does not affected by the `ex_ms` argument.)
            - If `<datetime.datetime>`, the key will expire at the given datetime.
              (Does not affected by the `ex_ms` argument.)

        :param ex_ms: `<bool>` Whether the expiry is in milliseconds.
            - If `False` (default), the expiry is in seconds.
            - If `True`, the expiry is in milliseconds.
            - Only takes effect when `ex` is `<int>` / `<float>` / `<str>`.

        :param deserialize: `<bool>` Whether to deserialize the value to its original (or compatiable) python dtype.
            - If `True` (default), thie method will try to deserialize and reconstruct
              the value to its original (or compatiable) python dtype. `NOTICE`: the key
              must be set by `x_set()` or `x_setget()` method with `serialize=True`.
            - If `False`, this method works the same as the native `get` method.
              and returns the value in `bytes` or `None`.

        :param raise_error: `<bool>` Whether to raise errors if the operation failed.
            - If `True` (default), raise errors.
            - If `False`, log the error as warrning and return `None`.

        :return: The value of the key, or `None` if the key does not exist.
        """
        args: list = ["PERSIST"] if ex is None else parse_ex(ex, ex_ms)
        try:
            return deserialize_cond(
                self.execute_command("GETEX", key, *args), deserialize
            )
        except Exception as err:
            return handle_exc(err, "x_getex", raise_error)

    def x_expiry(
        self,
        key: str,
        format: Literal["ttl", "ts", "dt"] | None = None,
        ms: bool = False,
        raise_error: bool = True,
    ) -> int | float | datetime.datetime | None:
        """Get the expiry of a key in Redis.

        :param key: `<str>` The redis key to get expiry.
        :param format: `<str>` The format of the returned expiry, accepts:
            - `None` or `"ttl"` (default), return the expiry in seconds.
              Equivalent to the native `ttl` command.
            - `"ts"`, return the expiry in timestamp.
              Equivalent to the native `expiretime` command.
            - `"dt"`, return the expiry in datetime.
              Convert the timestamp to datetime and return.

        :param raise_error: `<bool>` Whether to raise errors if the operation failed.
            - If `True` (default), raise errors.
            - If `False`, log the error as warrning and return `None`.

        :return: The expiry of the key in `<int>` or `<datetime.datetime>`.
            - If the key does not exist, always return -2.
            - If the key is persistent, always return -1.
        """
        if format is None or format == "ttl":
            try:
                return self.execute_command("PTTL" if ms else "TTL", key)
            except Exception as err:
                return handle_exc(err, "x_expiry", raise_error)
        elif ms:
            try:
                value = self.execute_command("PEXPIRETIME", key) / 1000
            except Exception as err:
                return handle_exc(err, "x_expiry", raise_error)
        else:
            try:
                value = self.execute_command("EXPIRETIME", key)
            except Exception as err:
                return handle_exc(err, "x_expiry", raise_error)
        if format == "dt" and value > 0:
            return timestamp_to_datetime(value)
        else:
            return value

    # Set command
    def x_set(
        self,
        key: str,
        value: Any,
        ex: Literal["KEEPTTL"]
        | int
        | float
        | datetime.timedelta
        | datetime.datetime
        | None = None,
        ex_ms: bool = False,
        set_on: Literal["XX", "NX"] | None = None,
        serialize: bool = True,
        raise_error: bool = True,
    ) -> bool | None:
        """Set the value at the key in Redis.

        :param key: `<str>` The redis key to set.
        :param value: The value to set to the key, accepts:
            - `<str>` / `<int>` / `<float>` / `<bytes>`
            - For more data types, see the `serialize` argument.

        :param ex: The expiry, accepts:
            - If `None` (default), the key will be persistent.
            - If `"KEEPTTL"`, retain the key original expiry if already exist
              else set the expiry to persistent.
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

        :param set_on: `<str>` Specify set behavior base on key existance.
            - If `None` (default), set the key regardless of the existance of the key.
            - If `"XX"`, set the key only if the key already exists.
            - If `"NX"`, set the key only if the key does not exists.

        :param serialize: `<bool>` Whether to serialize the value to bytes.
            - If `True` (default), this method can handle extra data types, such as:
              `datetime.datetime`, `numpy.ndarray`, `pandas.DataFrame`, etc. `NOTICE`:
              the key value should only be get through `x_get()` method with
              `deserialize=True`, which will deserialized and reconstructed the
              value to its original (or compatiable) python dtype.
            - If `False`, this method works the same as the native `set` method.

        :param raise_error: `<bool>` Whether to raise errors if the operation failed.
            - If `True` (default), raise errors.
            - If `False`, log the error as warrning and return `None`.

        :return: `<bool>` Whether the value was set.
        """
        try:
            value = serialize_cond(value, serialize)
        except Exception as err:
            return handle_exc(err, "x_set", raise_error)
        args: list = [key, value]
        if ex is not None:
            if ex == "KEEPTTL":
                args.append(ex)
            else:
                args += parse_ex(ex, ex_ms)
        if set_on is not None:
            args.append(set_on)
        try:
            return bool(self.execute_command("SET", *args))
        except Exception as err:
            return handle_exc(err, "x_set", raise_error)

    def x_setget(
        self,
        key: str,
        value: Any,
        ex: Literal["KEEPTTL"]
        | int
        | float
        | datetime.timedelta
        | datetime.datetime
        | None = None,
        ex_ms: bool = False,
        set_on: Literal["XX", "NX"] | None = None,
        serialize: bool = True,
        raise_error: bool = True,
    ) -> bytes | None:
        """Set the value at the key in Redis and get the original value.

        :param key: `<str>` The redis key to set/get.
        :param value: The value to set to the key, accepts:
            - `<str>` / `<int>` / `<float>` / `<bytes>`
            - For more data types, see the `serialize` argument.

        :param ex: The expiry, accepts:
            - If `None` (default), the key will be persistent.
            - If `"KEEPTTL"`, retain the key original expiry if already exist
              else set the expiry to persistent.
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

        :param set_on: `<str>` Specify set behavior base on key existance.
            - If `None` (default), set the key regardless of the existance of the key.
            - If `"XX"`, set the key only if the key already exists.
            - If `"NX"`, set the key only if the key does not exists.

        :param serialize: `<bool>` Whether to serialize/deserialize the value.
            - If `True` (default), this method will serialize the value to bytes before
              set to the key, which allows it to handle extra data types, such as:
              `datetime.datetime`, `numpy.ndarray`, `pandas.DataFrame`, etc. And
              deserialize the value to its original (or compatiable) python dtype
              when getting the original value.
            - If `False`, this method works the same as the native `set` method with
              `get=True`.

        :param raise_error: `<bool>` Whether to raise errors if the operation failed.
            - If `True` (default), raise errors.
            - If `False`, log the error as warrning and return `None`.

        :return: `<bytes>` The original value of the key, or `None` if the key does not exist.
        """
        try:
            value = serialize_cond(value, serialize)
        except Exception as err:
            return handle_exc(err, "x_setget", raise_error)

        args: list = [key, value]
        if ex is not None:
            if ex == "KEEPTTL":
                args.append(ex)
            else:
                args += parse_ex(ex, ex_ms)
        if set_on is not None:
            args.append(set_on)
        try:
            return deserialize_cond(self.execute_command("SET", *args), serialize)
        except Exception as err:
            return handle_exc(err, "x_setget", raise_error)

    def x_expire(
        self,
        key: str,
        ex: int | str | float | datetime.timedelta | datetime.datetime | None,
        ex_ms: bool = False,
        set_on: Literal["XX", "NX", "GT", "LT"] | None = None,
        raise_error: bool = True,
    ) -> bool | None:
        """Set the expiry of a key in Redis.

        :param key: `<str>` The redis key to set expiry.
        :param ex: The expiry in seconds, accepts:
            - If `None`, set the key to be persistent.
            - If `<int>` / `<float>` / `<str>`, the key will expire after the given
              number of seconds. (Float values will be rounded to integers.)
            - If `<datetime.timedelta>`, the key will expire after delta's total seconds.
            - If `<datetime.datetime>`, the key will expire at the given datetime.

        :param ex_ms: `<bool>` Whether the expiry is in milliseconds.
            - If `False` (default), the expiry is in seconds.
            - If `True`, the expiry is in milliseconds.
            - Only takes effect when `ex` is `<int>` / `<float>` / `<str>`.

        :param set_on: `<str>` Specify how to set key expiry.
            - If `None` (default), set the new expiry regardless of the expiry of the key.
            - If `"XX"`, set the new expiry only if the key already has expiry.
            - If `"NX"`, set the new expiry only if the key has no expiry.
            - If `"GT"`, set the new expiry only if the new expiry is greater than current one.
            - If `"LT"`, set the new expiry only if the new expiry is less than current one.

        :param raise_error: `<bool>` Whether to raise errors if the operation failed.
            - If `True` (default), raise errors.
            - If `False`, log the error as warrning and return `None`.

        :return: `<bool>` Whether the expiry was set.
        """
        if ex is None:
            try:
                return bool(self.execute_command("PERSIST", key))
            except Exception as err:
                return handle_exc(err, "x_expire", raise_error)
        else:
            args = parse_expire_ex(key, ex, ex_ms)
            if set_on is not None:
                args.append(set_on)
            try:
                return bool(self.execute_command(*args))
            except Exception as err:
                return handle_exc(err, "x_expire", raise_error)

    # Del commands
    def x_del(self, *keys: str, raise_error: bool = True) -> int | None:
        """Delete one or more keys in Redis.

        :param keys: `<str>` The redis keys to delete.
        :param raise_error: `<bool>` Whether to raise errors if the operation failed.
            - If `True` (default), raise errors.
            - If `False`, log the error as warrning and return `None`.

        :return: `<int>` Number of keys been deleted.
        """
        if not keys:
            return 0
        try:
            return self.execute_command("DEL", *keys)
        except Exception as err:
            return handle_exc(err, "x_del", raise_error)

    def x_delptn(
        self,
        pattern: str,
        count: int | None = None,
        type_: Literal["STRING", "LIST", "SET", "ZSET", "HASH", "STREAM"] | None = None,
        raise_error: bool = True,
    ) -> int | None:
        """Delete keys matched by pattern in Redis.

        :param pattern: `<str>` The pattern to match, e.g. `user:*`.
        :param count: The hint to the number of elements to return at every iteration.
        :param type_: The type of keys to match, accepts: `"STRING"`, `"LIST"`, `"SET"`, `"ZSET"`, `"HASH"`, `"STREAM"` and `None`
        :param raise_error: `<bool>` Whether to raise errors if the operation failed.
            - If `True` (default), raise errors.
            - If `False`, log the error as warrning and return `None`.

        :return: `<int>` Number of keys matched by the pattern been deleted.
        """
        return self.x_del(
            *self.x_scan_iter(
                pattern, count=count, type_=type_, raise_error=raise_error
            ),
            raise_error=raise_error,
        )

    # Check commands
    def x_exists(self, *keys: str, raise_error: bool = True) -> int | None:
        """Return the number of provided keys exist in Redis.

        :param keys: `<str>` The redis keys to check.
        :param raise_error: `<bool>` Whether to raise errors if the operation failed.
            - If `True` (default), raise errors.
            - If `False`, log the error as warrning and return `None`.

        :return: `<int>` Number of keys existing.
        """
        try:
            return self.execute_command("EXISTS", *keys)
        except Exception as err:
            return handle_exc(err, "x_exists", raise_error)

    def x_cntptn(
        self,
        pattern: str,
        count: int | None = None,
        type_: Literal["STRING", "LIST", "SET", "ZSET", "HASH", "STREAM"] | None = None,
        raise_error: bool = True,
    ) -> int | None:
        """Return the number of keys matched by the pattern in Redis.

        :param pattern: `<str>` The pattern to match, e.g. `user:*`.
        :param count: The hint to the number of elements to return at every iteration.
        :param type_: The type of keys to match, accepts: `"STRING"`, `"LIST"`, `"SET"`, `"ZSET"`, `"HASH"`, `"STREAM"` and `None`
        :param raise_error: `<bool>` Whether to raise errors if the operation failed.
            - If `True` (default), raise errors.
            - If `False`, log the error as warrning and return `None`.

        :return: `<int>` Number of keys matched by the pattern.
        """
        _count: int = 0
        for key in self.x_scan_iter(
            pattern, count=count, type_=type_, raise_error=raise_error
        ):
            if key:
                _count += 1
        return _count

    # Manipulate commands
    def x_incrby(
        self,
        key: str,
        amount: int = 1,
        raise_error: bool = True,
    ) -> int | None:
        """Increase the value (integer) of a key by a given amount in Redis.

        - The value of the key must be an integer.
        - If the key does not exist, will first initialized to 0 and then
          increase by the given amount.

        :param key: `<str>` The key to increase.
        :param amount: `<int>` The amount to increase by.
        :param raise_error: `<bool>` Whether to raise errors if the operation failed.
            - If `True` (default), raise errors.
            - If `False`, log the error as warrning and return `None`.

        :return: `<int>` The new value after increase operation.
        """
        try:
            return self.execute_command("INCRBY", key, amount)
        except Exception as err:
            return handle_exc(err, "x_incrby", raise_error)

    def x_decrby(
        self,
        key: str,
        amount: int = 1,
        raise_error: bool = True,
    ) -> int | None:
        """Decrease the value (integer) of a key by a given amount in Redis.

        - The value of the key must be an integer.
        - If the key does not exist, will first initialized to 0 and then
          decrease by the given amount.

        :param key: `<str>` The key to decrease.
        :param amount: `<int>` The amount to decrease by.
        :param raise_error: `<bool>` Whether to raise errors if the operation failed.
            - If `True` (default), raise errors.
            - If `False`, log the error as warrning and return `None`.

        :return: `<int>` The new value after decrease operation.
        """
        try:
            return self.execute_command("DECRBY", key, amount)
        except Exception as err:
            return handle_exc(err, "x_decrby", raise_error)

    # Scan commands
    def x_scan(
        self,
        cursor: int,
        pattern: str,
        count: int | None = None,
        type_: Literal["STRING", "LIST", "SET", "ZSET", "HASH", "STREAM"] | None = None,
        raise_error: bool = True,
        **kwargs,
    ) -> tuple[int, str | None]:
        """Incrementally return key names matched by pattern. Also return a cursor
        indicating the scan position.

        :param cursor: `<int>` The cursor to start the scan.
        :param pattern: `<str>` The pattern to match, e.g. `user:*`.
        :param count: The hint to the number of elements to return at every iteration.
        :param type_: The type of keys to match, accepts: `"STRING"`, `"LIST"`, `"SET"`, `"ZSET"`, `"HASH"`, `"STREAM"` and `None`
        :param raise_error: `<bool>` Whether to raise errors if the operation failed.
            - If `True` (default), raise errors.
            - If `False`, log the error as warrning and return `None`.

        :param kwargs: Additional arguments to pass to the Redis command.
        :return: `<tuple>` The cursor position and the name of the key.
        """
        args: list = [cursor, b"MATCH", pattern]
        if count is not None:
            args.extend([b"COUNT", count])
        if type_ is not None:
            args.extend([b"TYPE", type_])
        try:
            return self.execute_command("SCAN", *args, **kwargs)
        except Exception as err:
            return (0, handle_exc(err, "x_scan", raise_error))

    def x_scan_iter(
        self,
        pattern: str,
        count: int | None = None,
        type_: Literal["STRING", "LIST", "SET", "ZSET", "HASH", "STREAM"] | None = None,
        raise_error: bool = True,
        **kwargs,
    ) -> Iterator[str | None]:
        """Make an iterator of 'x_scan' so that the client doesn't
        need to remember the cursor position.

        :param pattern: `<str>` The pattern to match, e.g. `user:*`.
        :param count: The hint to the number of elements to return at every iteration.
        :param type_: The type of keys to match, accepts: `"STRING"`, `"LIST"`, `"SET"`, `"ZSET"`, `"HASH"`, `"STREAM"` and `None`
        :param raise_error: `<bool>` Whether to raise errors if the operation failed.
            - If `True` (default), raise errors.
            - If `False`, log the error as warrning and stop the iteration and return `None`.

        :param kwargs: Additional arguments to pass to the Redis command.
        :return: The name of the key as an `Iterator[str]`.
        """
        cursor = "0"
        while cursor != 0:
            cursor, data = self.x_scan(
                cursor,
                pattern,
                count=count,
                type_=type_,
                raise_error=raise_error,
                **kwargs,
            )
            yield from data

    # Decorator methods
    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a Redis key based on prefix, args and kwargs.

        :param prefix: The unique prefix for the redis key.
        :param args: The arguments of a function.
        :param kwargs: The keyword arguments of a function.
        :return: The redis key.

        - Each arguments and keyword arguments are converted to string,
        and concatenated with `":"`.
        - The key is formatted to `prefix:args:kwargs:`, and always ends
        with `":"` to avoid collisions.

        ### Example
        >>> key = generate_key("pref", 1, 2, 3, a=1, b=2, c=3)
        >>> "pref:1:2:3:a1:b2:c3:"
        """
        return generate_key(prefix, args, kwargs)

    def serialize(self, value: Any) -> bytes:
        """Serielize an value to bytes.

        ### Supported data types includes:
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

        :param value: The value to be serialized.
        :raises DataError: If any error occurs.
        :return: `<bytes>` The serialized data.
        """
        return serialize(value)

    def deserialize(self, value: bytes) -> Any:
        """Deserialize the value to its original (or compatible) python dtype.
        Must be used with the `serialize` function in this module.
        """
        return deserialize(value)

    def decor_cache_get(
        self,
        key: str,
        ex: int | str | float | datetime.timedelta | datetime.datetime,
        ex_ms: bool,
        ex_rf: bool,
    ) -> Any | None:
        """Get method for cache decorator. (Internal use only)."""
        # Get value
        try:
            # . refresh expiry
            if ex_rf:
                value = self.execute_command("GETEX", key, *parse_ex(ex, ex_ms))
            # . get directly
            else:
                value = self.execute_command("GET", key)
        except Exception as err:
            logger.warning(f"Redis <decorator.cache.get> error: {err}")
            return None
        if value is None:
            return None
        # Deserialize
        try:
            return deserialize(value)
        except Exception as err:
            logger.warning(f"Redis <decorator.cache.deserialize> error: {err}")
            return None

    def decor_cache_set(
        self,
        key: str,
        value: Any,
        ex: int | str | float | datetime.timedelta | datetime.datetime,
        ex_ms: bool,
    ) -> None:
        """Set method for cache decorator. (Internal use only)."""
        # Serialize
        try:
            value = serialize(value)
        except Exception as err:
            logger.warning(f"Redis <decorator.cache.serialize> error: {err}")
            return None
        # Set value
        try:
            self.execute_command("SET", key, value, *parse_ex(ex, ex_ms))
            return None
        except Exception as err:
            logger.warning(f"Redis <decorator.cache.set> error: {err}")
            return None

    def decor_update_exists(self, key: str) -> bool:
        """Exists method for update decorator. (Internal use only)."""
        try:
            return bool(self.execute_command("EXISTS", key))
        except Exception as err:
            logger.warning(f"Redis <decorator.update.exists> error: {err}")
            return False

    def decor_update_set(self, key: str, value: Any) -> bool | None:
        """Set method for update decorator. (Internal use only)."""
        # Serialize
        try:
            value = serialize(value)
        except Exception as err:
            logger.warning(f"Redis <decorator.update.serialize> error: {err}")
            return None
        # Set value
        try:
            return bool(self.execute_command("SET", key, value, "KEEPTTL", "XX"))
        except Exception as err:
            logger.warning(f"Redis <decorator.update.set> error: {err}")
            return None

    def decor_delete(self, key: str) -> bool | None:
        """Delete method for update decorator. (Internal use only)."""
        try:
            return bool(self.execute_command("DEL", key))
        except Exception as err:
            logger.warning(f"Redis <decorator.delete> error: {err}")
            return None


# Get client
def get_client(
    host: str = "localhost",
    port: int = 6379,
    db: int = 0,
    retry_on_timeout: bool = False,
    retry_on_error: list[Exception] | None = None,
    retry: Retry | None = None,
    encoding: str = "utf-8",
    encoding_errors: Literal["strict", "ignore", "replace"] = "strict",
    username: str | None = None,
    password: str | None = None,
    unix_socket_path: str | None = None,
    socket_timeout: int | float | None = None,
    socket_connect_timeout: int | float | None = None,
    socket_keepalive: bool | None = None,
    socket_keepalive_options: dict[str, float] | None = None,
    connection_pool: ConnectionPool | None = None,
    max_connections: int | None = None,
    single_connection_client: bool = False,
    ssl: bool = False,
    ssl_keyfile: str | None = None,
    ssl_password: str | None = None,
    ssl_cert_reqs: Literal["none", "optional", "required"] = "required",
    ssl_certfile: str | None = None,
    ssl_ca_certs: str | None = None,
    ssl_ca_path: str | None = None,
    ssl_ca_data: str | bytes | None = None,
    ssl_check_hostname: bool = False,
    ssl_validate_ocsp: bool = False,
    ssl_validate_ocsp_stapled: bool = False,
    ssl_ocsp_context: object | None = None,
    ssl_ocsp_expected_cert: str | None = None,
    health_check_interval: int | float = 0,
    client_name: str | None = None,
    redis_connect_func: Callable | None = None,
    credential_provider: CredentialProvider | None = None,
    protocol: int | None = 2,
) -> Redis:
    """Get the Redis client which decorators in this package will use.

    The `<Redis>` object is a subclass of `reids.StricRedis`.
    Decorators in this package requires this subclass to work. Besides some
    added methods, and `decode_responses=False`, this subclass works the same
    as the native `redis.StrictRedis` class.
    """
    return Redis(
        host=host,
        port=port,
        db=db,
        retry_on_timeout=retry_on_timeout,
        retry_on_error=retry_on_error,
        retry=retry,
        encoding=encoding,
        encoding_errors=encoding_errors,
        username=username,
        password=password,
        unix_socket_path=unix_socket_path,
        socket_timeout=socket_timeout,
        socket_connect_timeout=socket_connect_timeout,
        socket_keepalive=socket_keepalive,
        socket_keepalive_options=socket_keepalive_options,
        connection_pool=connection_pool,
        max_connections=max_connections,
        single_connection_client=single_connection_client,
        ssl=ssl,
        ssl_keyfile=ssl_keyfile,
        ssl_password=ssl_password,
        ssl_cert_reqs=ssl_cert_reqs,
        ssl_certfile=ssl_certfile,
        ssl_ca_certs=ssl_ca_certs,
        ssl_ca_path=ssl_ca_path,
        ssl_ca_data=ssl_ca_data,
        ssl_check_hostname=ssl_check_hostname,
        ssl_validate_ocsp=ssl_validate_ocsp,
        ssl_validate_ocsp_stapled=ssl_validate_ocsp_stapled,
        ssl_ocsp_context=ssl_ocsp_context,
        ssl_ocsp_expected_cert=ssl_ocsp_expected_cert,
        health_check_interval=health_check_interval,
        client_name=client_name,
        redis_connect_func=redis_connect_func,
        credential_provider=credential_provider,
        protocol=protocol,
    )
