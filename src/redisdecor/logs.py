# /usr/bin/python
# -*- coding: UTF-8 -*-
import logging

# Package logger
logger = logging.getLogger(__package__)
__log_format = logging.Formatter(
    "%(asctime)s %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
logger.setLevel(logging.INFO)
__handler = logging.StreamHandler()
__handler.setFormatter(__log_format)
logger.addHandler(__handler)
