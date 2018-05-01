# coding=utf-8

import struct


def get_int_from_bytes(data):
    if len(data) == 2:
        return struct.unpack('>h', data)[0]
    if len(data) == 4:
        return struct.unpack('>i', data)[0]
    return 0


def get_string_from_bytes(data):
    return data.decode('utf-8')
