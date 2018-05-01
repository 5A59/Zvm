# coding=utf-8

from base.stack import Stack
from java_class import class_file, class_parser
import struct


class Thread(object):
    def __init__(self):
        self.pc = 0
        self.stack = JavaStack()


class JavaStack(object):
    def __init__(self):
        self.__frames = []


class Frame(object):
    def __init__(self, local_var_size, operand_stack_size):
        self.local_vars = LocalVars(local_var_size)
        self.operand_stack = OperandStack(operand_stack_size)
        self.dynamic_linking = DynamicLinking()


class Slot(object):
    def __init__(self):
        self.num = None
        self.ref = None


# 局部变量表
class LocalVars(object):
    def __init__(self, size):
        self.__size = size
        self.__items = [None] * size
        for i in range(size):
            self.__items[i] = Slot()

    def test_get_items(self):
        return self.__items

    def __add_num_to_item(self, index, data):
        slot = self.__items[index]
        slot.num = data

    def __get_num_from_item(self, index):
        return self.__items[index].num

    def __add_ref_to_item(self, index, ref):
        slot = self.__items[index]
        slot.ref = ref

    def __get_ref_from_item(self, index):
        return self.__items[index].ref

    def add_int(self, index, data):
        self.__add_num_to_item(index, struct.pack('i', data))

    def get_int(self, index):
        return struct.unpack('i', self.__get_num_from_item(index))

    def add_long(self, index, data):
        packed = struct.pack('q', data)
        self.__add_num_to_item(index, packed[:4])
        self.__add_num_to_item(index + 1, packed[4:])

    def get_long(self, index):
        first = self.__get_num_from_item(index)
        last = self.__get_num_from_item(index + 1)
        return struct.unpack('q', first + last)

    # TODO: python3 里 float 也是 8 字节，float 精度存疑
    def add_float(self, index, data):
        self.__add_num_to_item(index, struct.pack('f', data))

    def get_float(self, index):
        return struct.unpack('f', self.__get_num_from_item(index))

    def add_double(self, index, data):
        packed = struct.pack('d', data)
        self.__add_num_to_item(index, packed[:4])
        self.__add_num_to_item(index + 1, packed[4:])

    def get_double(self, index):
        first = self.__get_num_from_item(index)
        last = self.__get_num_from_item(index + 1)
        return struct.unpack('d', first + last)

    def add_ref(self, index, ref):
        self.__add_ref_to_item(index, ref)

    def get_ref(self, index):
        return self.__get_ref_from_item(index)


class Entry(object):
    def __init__(self, data):
        self.data = data


# 操作数栈 TODO: 暂时不区分数据类型，靠调用者保证
class OperandStack(object):
    def __init__(self, size):
        self.__size = size
        self.__stack = Stack()

    def push(self, data):
        entry = Entry(data)
        self.__stack.push(entry)

    def pop(self):
        return self.__stack.pop().data

    def push_int(self, data):
        self.push(data)

    def pop_int(self):
        return self.pop()

    def push_long(self, data):
        self.push(data)

    def pop_long(self):
        return self.pop()

    def push_float(self, data):
        self.push(data)

    def pop_float(self):
        return self.pop()

    def push_double(self, data):
        self.push(data)

    def pop_double(self):
        return self.pop()


class DynamicLinking(object):
    def __init__(self):
        pass


def test_local_var():
    local_vars = LocalVars(9)
    local_vars.add_long(0, 2147483680)
    print(local_vars.get_long(0))

    local_vars.add_int(2, 8)
    print(local_vars.get_int(2))

    local_vars.add_double(3, 2147483680.1231231312)
    print(local_vars.get_double(3))

    local_vars.add_float(5, 8.111)
    print(local_vars.get_float(5))


def test_main():
    pass


if __name__ == "__main__":
    # test_local_var()
    test_main()
