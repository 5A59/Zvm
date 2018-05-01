# coding=utf-8

import abc


class Instruction(mateclass=abc.ABCMeta):
    def __init__(self):
        self.code = None  # 字节码
        self.name = None  # 助记符

    @abc.abstractmethod
    def execute(self):
        pass


class NOP(Instruction):
    def __init__(self):
        super(NOP, self).__init__()

    def execute(self):
        pass
