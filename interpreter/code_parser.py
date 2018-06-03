# coding=utf-8

from base.utils import print_utils, error_handler


class CodeParser(object):
    def __init__(self, code):
        self.code = code
        self.pc = 0

    def reset(self, code, pc):
        self.code = code
        self.pc = pc

    def check_pc(self):
        if self.pc >= len(self.code):
            print_utils.print_error("pc out of index in code parser")
            error_handler.rise_runtime_error("pc out of index in code parser")

    def read_code(self):
        self.check_pc()
        ins = self.code[self.pc]
        self.pc += 1
        return ins

    # 读操作数
    def read_op(self):
        self.check_pc()
        op = self.code[self.pc]
        self.pc += 1
        return op
