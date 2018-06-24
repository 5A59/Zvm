# coding=utf-8

from base.utils.print_utils import print_jvm_status


class Stack(object):
    def __init__(self):
        self.__items = []

    def items(self):
        return self.__items

    def get_val_at(self, index):
        return self.__items[len(self.__items) - index - 1]

    def print_state(self):
        print_jvm_status(self.__items)

    def push(self, data):
        self.__items.append(data)

    def size(self):
        return len(self.__items)

    def peek(self):
        return self.__items[self.size() - 1]

    def pop(self):
        return self.__items.pop()

    def clear(self):
        self.__items.clear()
