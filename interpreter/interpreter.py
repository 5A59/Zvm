# coding=utf-8

from runtime.thread import Thread, Frame, JavaStack
from runtime.jclass import Method
from base.utils import print_utils, error_handler
from instruction import instruction
from interpreter.code_parser import CodeParser


class Interpreter(object):
    def __init__(self):
        self.thread = None

    def run(self, method):
        self.thread = Thread.new_thread()
        thread = self.thread
        frame = Frame(thread, method)
        thread.add_frame(frame)
        code_parser = CodeParser(method.code)
        while True:
            if not thread.has_frame():
                break
            frame = thread.top_frame()
            method = frame.method
            code_parser.reset(method.code, frame.pc)
            ins_code = code_parser.read_code()
            print_utils.print_msg(ins_code)
            ins = instruction.get_instruction(ins_code)
            ins.read_operands(code_parser)
            ins.execute_wrapper(frame)
            frame.pc = code_parser.pc

