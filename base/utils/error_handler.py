# coding=utf-8


def rise_runtime_error(msg):
    raise RuntimeError("jvm internal error: " + msg)


def rise_null_point_error():
    raise RuntimeError("error: java.lang.NullPointerException")


def rise_class_cast_error():
    raise RuntimeError("error: java.lang.ClassCastException")


def rise_error(error):
    raise error


class InternalError(Exception):
    pass


class OutOfMemoryError(Exception):
    pass


class StackOverflowError(Exception):
    pass


class UnknownError(Exception):
    pass
