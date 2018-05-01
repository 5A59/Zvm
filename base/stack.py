# coding=utf-8


class Stack(object):
    def __init__(self):
        self.__items = []

    def push(self, data):
        self.__items.append(data)

    def size(self):
        return len(self.__items)

    def peek(self):
        return self.__items[self.size() - 1]

    def pop(self):
        return self.__items.pop()
