# cython: language_level=3
# cython: wraparound=False
# cython: boundscheck=False

# Cython imports
import cython
from cython.cimports.cpython import datetime  # type: ignore
from cython.cimports.cpython.int import PyInt_Check as is_int  # type: ignore
from cython.cimports.cpython.float import PyFloat_Check as is_float  # type: ignore
from cython.cimports.cpython.string import PyString_Check as is_str  # type: ignore
from cython.cimports.serializor import transcode  # type: ignore
from cython.cimports.cytimes import cydatetime as cydt  # type: ignore

datetime.import_datetime()

# Python imports
import datetime
from redis import DataError
from serializor import transcode
from cytimes import cydatetime as cydt
from redisdecor.logs import logger


# Serialization
@cython.ccall
def serialize(value: object) -> object:
    try:
        return transcode.encode(value)
    except Exception as err:
        raise DataError(err) from err


@cython.ccall
def serialize_cond(value: object, s: cython.bint) -> object:
    try:
        return transcode.encode(value) if s else value
    except Exception as err:
        raise DataError(err) from err


@cython.ccall
def deserialize(value: object) -> object:
    try:
        return transcode.decode(value)
    except Exception as err:
        raise DataError(err) from err


@cython.ccall
def deserialize_cond(value: object, ds: cython.bint) -> object:
    try:
        return transcode.decode(value) if ds and value is not None else value
    except Exception as err:
        raise DataError(err) from err


# Arguments
@cython.ccall
def parse_ex(ex: object, ex_ms: cython.bint) -> list:
    # Eexpire when (datetime)
    if cydt.is_dt(ex):
        if ex_ms:
            vals = int(cydt.dt_to_timestamp(ex) * 1000)
            flag = "PXAT"
        else:
            vals = int(cydt.dt_to_timestamp(ex))
            flag = "EXAT"

    # Expire after (int / timedelta / str / float)
    else:
        flag = "PX" if ex_ms else "EX"
        # Integer
        if is_int(ex):
            vals = ex
        # Timedelta
        elif cydt.is_delta(ex):
            if ex_ms:
                vals = cydt.delta_to_microseconds(ex) // cydt.US_MILLISECOND
            else:
                vals = cydt.delta_to_microseconds(ex) // cydt.US_SECOND
        # String
        elif is_str(ex):
            try:
                vals = int(ex)
            except Exception:
                try:
                    vals = int(float(ex))
                except Exception as err:
                    raise DataError("Invalid 'ex' value %s." % repr(ex)) from err
        # Float
        elif is_float(ex):
            vals = int(ex)
        # Invalid
        else:
            raise DataError(
                "Argument 'ex' must be type of: `<int>`, `<float>`, `<str>`, `<datetime.timedelta>`, or `<datetime.datetime>`"
            )

    # Return
    return [flag, vals]


@cython.ccall
def parse_expire_ex(key: str, ex: object, ex_ms: cython.bint) -> list:
    # Expire when (datetime)
    if cydt.is_dt(ex):
        if ex_ms:
            vals = int(cydt.dt_to_timestamp(ex) * 1000)
            flag = "PEXPIREAT"
        else:
            vals = int(cydt.dt_to_timestamp(ex))
            flag = "EXPIREAT"

    # Expire after (int / timedelta / str / float)
    else:
        flag = "PEXPIRE" if ex_ms else "EXPIRE"
        # Integer
        if is_int(ex):
            vals = ex
        # Timedelta
        elif cydt.is_delta(ex):
            if ex_ms:
                vals = cydt.delta_to_microseconds(ex) // cydt.US_MILLISECOND
            else:
                vals = cydt.delta_to_microseconds(ex) // cydt.US_SECOND
        # String
        elif is_str(ex):
            try:
                vals = int(ex)
            except Exception:
                try:
                    vals = int(float(ex))
                except Exception as err:
                    raise DataError("Invalid 'ex' value %s." % repr(ex)) from err
        # Float
        elif is_float(ex):
            vals = int(ex)
        # Invalid
        else:
            raise DataError(
                "Argument 'ex' must be type of: `<int>`, `<float>`, `<str>`, `<datetime.timedelta>`, or `<datetime.datetime>`"
            )

    # Return
    return [flag, key, vals]


# Conversion
@cython.ccall
def timestamp_to_datetime(timestamp: object) -> datetime.datetime:
    return cydt.dt_fr_timestamp(timestamp, None)


# Decorator
@cython.ccall
def generate_key(prefix: str, args: tuple, kwargs: dict) -> str:
    # Arguments
    args_key: str
    if args:
        args_: list = []
        for i in args:
            args_.append(str(i))
        args_key = ":".join(args_)
    else:
        args_key = ""

    # Keyword arguments
    kwargs_key: str
    if kwargs:
        kwargs_: list = []
        for k, v in kwargs.items():
            k_: str = str(k)
            v_: str = str(v)
            kwargs_.append(k_ + v_)
        kwargs_key = ":".join(kwargs_)
    else:
        kwargs_key = ""

    # Concat keys
    return "%s:%s:%s:" % (prefix, args_key, kwargs_key)


# Exceptions
def handle_exc(exc: Exception, src: str, raise_error: cython.bint) -> None:
    if raise_error:
        raise exc
    else:
        logger.warning(f"Redis <{src}> error: {type(exc)} {exc}")
        return None
