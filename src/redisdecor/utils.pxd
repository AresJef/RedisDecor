# cython: language_level=3

from cpython cimport datetime

cpdef object serialize(object value) except *
cpdef object serialize_cond(object value, bint s) except *
cpdef object deserialize(object value) except *
cpdef object deserialize_cond(object value, bint ds) except *
cpdef list parse_ex(object ex, bint ex_ms) except *
cpdef list parse_expire_ex(str key, object ex, bint ex_ms) except *
cpdef datetime.datetime timestamp_to_datetime(object timestamp) except *
cpdef str generate_key(str prefix, tuple args, dict kwargs) except *
