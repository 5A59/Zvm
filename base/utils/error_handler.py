# coding=utf-8


def rise_runtime_error(msg):
    raise RuntimeError("error: " + msg)


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
