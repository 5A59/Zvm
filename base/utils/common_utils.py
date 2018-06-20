# coding=utf-8

import struct


# 主要是给跳转指令用
def get_short_from_bytes(byte1, byte2):
    val = (byte1 << 8) | byte2
    return struct.unpack('>h', val.to_bytes(2, byteorder='big'))[0]


def get_int_from_bytes(data):
    if len(data) == 2:
        return struct.unpack('>h', data)[0]
    if len(data) == 4:
        return struct.unpack('>i', data)[0]
    return 0


def get_float_from_bytes(data):
    return struct.unpack('>f', data)[0]


def get_long_from_bytes(high, low):
    return struct.unpack('>q', high + low)[0]


def get_double_from_bytes(high, low):
    return struct.unpack('>d', high + low)[0]


def get_string_from_bytes(data):
    return data.decode('utf-8')
