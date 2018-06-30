# coding=utf-8

from base.utils import print_utils, error_handler
import ctypes


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

    def jump_by(self, off):
        self.pc += off

    # switch 指令使用  使得地址都是 4 的倍数
    def skip_padding(self):
        while self.pc % 4 != 0:
            self.read_op()

    def read_4byte(self):
        byte1 = self.read_op()
        byte2 = self.read_op()
        byte3 = self.read_op()
        byte4 = self.read_op()
        byte = (byte1 << 24) | (byte2 << 16) | (byte3 << 8) | byte4
        return ctypes.c_int32(byte).value
