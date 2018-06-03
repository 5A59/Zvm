# coding=utf-8

import abc

from runtime.thread import Frame, LocalVars
from base.utils import print_utils, common_utils
from interpreter.code_parser import CodeParser


class Instruction(object):
    code = None  # 字节码
    name = None  # 助记符

    def read_operands(self, code_parser):
        pass

    def execute_wrapper(self, frame):
        print_utils.print_msg('\nexecute ins: ' + self.name)
        # frame.print_cur_state()
        self.execute(frame)

    @abc.abstractmethod
    def execute(self, frame):
        pass


class AALOAD(Instruction):
    code = 0x32
    name = 'aaload'

    def execute(self, frame):
        pass


class ICONST_I(Instruction):
    def __init__(self):
        super(ICONST_I, self).__init__()

    @abc.abstractmethod
    def get_index(self):
        pass

    def execute(self, frame):
        index = self.get_index()
        stack = frame.operand_stack
        stack.push_int(index)


class ICONST_M1(ICONST_I):
    code = 0x2
    name = 'iconst_m1'

    def __init__(self):
        super(ICONST_M1, self).__init__()

    def get_index(self):
        return -1


class ICONST_0(ICONST_I):
    code = 0x3
    name = 'iconst_0'

    def __init__(self):
        super(ICONST_0, self).__init__()

    def get_index(self):
        return 0


class ICONST_1(ICONST_I):
    code = 0x4
    name = 'iconst_1'

    def __init__(self):
        super(ICONST_1, self).__init__()

    def get_index(self):
        return 1


class ICONST_2(ICONST_I):
    code = 0x5
    name = 'iconst_2'

    def __init__(self):
        super(ICONST_2, self).__init__()

    def get_index(self):
        return 2


class ICONST_3(ICONST_I):
    code = 0x6
    name = 'iconst_3'

    def __init__(self):
        super(ICONST_3, self).__init__()

    def get_index(self):
        return 3


class ICONST_4(ICONST_I):
    code = 0x7
    name = 'iconst_4'

    def __init__(self):
        super(ICONST_4, self).__init__()

    def get_index(self):
        return 4


class ICONST_5(ICONST_I):
    code = 0x8
    name = 'iconst_5'

    def __init__(self):
        super(ICONST_5, self).__init__()

    def get_index(self):
        return 5


class ILOAD_N(Instruction):
    def __init__(self):
        super(ILOAD_N, self).__init__()

    @abc.abstractmethod
    def get_index(self):
        pass

    def execute(self, frame):
        index = self.get_index()
        local_vars = frame.local_vars
        operand_stack = frame.operand_stack
        value = local_vars.get_int(index)
        operand_stack.push_int(value)


class ILOAD_0(ILOAD_N):
    code = 0x1a
    name = 'iload_0'

    def __init__(self):
        super(ILOAD_0, self).__init__()

    def get_index(self):
        return 0


class ILOAD_1(ILOAD_N):
    code = 0x1b
    name = 'iload_1'

    def __init__(self):
        super(ILOAD_1, self).__init__()

    def get_index(self):
        return 1


class IADD(Instruction):
    code = 0x60
    name = 'iadd'

    def __init__(self):
        super(IADD, self).__init__()

    def execute(self, frame):
        operand_stack = frame.operand_stack
        val1 = operand_stack.pop_int()
        val2 = operand_stack.pop_int()
        res = val1 + val2
        operand_stack.push_int(res)


class INVOKESPECIAL(Instruction):
    code = 0xb7
    name = 'invokespecial'

    def __init__(self):
        super(INVOKESPECIAL, self).__init__()
        self.index = -1

    def read_operands(self, code_parser):
        index1 = code_parser.read_op()
        index2 = code_parser.read_op()
        self.index = (index1 << 8) | index2

    def execute(self, frame):
        # TODO: 方法校验
        constant_pool = frame.method.jclass.constant_pool.constants
        n_method_ref = constant_pool[self.index]
        print_utils.print_msg('invokespecial: ' + n_method_ref.name)
        n_method = n_method_ref.resolve_method()
        n_frame = Frame(frame.thread, n_method)
        frame.thread.add_frame(n_frame)


class INVOKESTATIC(Instruction):
    code = 0xb8
    name = 'invokestatic'

    def __init__(self):
        super(INVOKESTATIC, self).__init__()
        self.index = -1

    def read_operands(self, code_parser):
        index1 = code_parser.read_op()
        index2 = code_parser.read_op()
        self.index = (index1 << 8) | index2

    def execute(self, frame):
        # TODO: 方法校验
        constant_pool = frame.method.jclass.constant_pool.constants
        n_method_ref = constant_pool[self.index]
        print_utils.print_msg('invokestatic: ' + n_method_ref.name)
        n_method = n_method_ref.resolve_method()
        n_frame = Frame(frame.thread, n_method)
        frame.thread.add_frame(n_frame)
        arg_desc = n_method.arg_desc
        i = -1
        for arg in arg_desc:
            i += 1
            if arg == 'I':
                value = frame.operand_stack.pop_int()
                n_frame.local_vars.add_int(i, value)


class IRETURN(Instruction):
    code = 0xac
    name = 'ireturn'

    def __init__(self):
        super(IRETURN, self).__init__()

    def execute(self, frame):
        frame.thread.pop_frame()
        r_value = frame.operand_stack.pop_int()
        c_frame = frame.thread.top_frame()
        c_frame.operand_stack.push_int(r_value)


class ISTORE_N(Instruction):
    def __init__(self):
        super(ISTORE_N, self).__init__()

    @abc.abstractmethod
    def get_index(self):
        pass

    def execute(self, frame):
        value = frame.operand_stack.pop_int()
        index = self.get_index()
        frame.local_vars.add_int(index, value)


class ISTORE(ISTORE_N):
    code = 0x36
    name = 'istore'

    def __init__(self):
        super(ISTORE, self).__init__()
        self.index = 0

    def read_operands(self, code_parser):
        self.index = code_parser.read_op()

    def get_index(self):
        return self.index


class ISTORE_0(ISTORE_N):
    code = 0x3b
    name = 'istore_0'

    def __init__(self):
        super(ISTORE_0, self).__init__()

    def get_index(self):
        return 0


class ISTORE_1(ISTORE_N):
    def __init__(self):
        super(ISTORE_1, self).__init__()
        self.code = 0x3c
        self.name = 'istore_1'

    def get_index(self):
        return 1


class ISTORE_2(ISTORE_N):
    code = 0x3d
    name = 'istore_2'

    def __init__(self):
        super(ISTORE_2, self).__init__()

    def get_index(self):
        return 2


class ISTORE_3(ISTORE_N):
    code = 0x3e
    name = 'istore_3'

    def __init__(self):
        super(ISTORE_3, self).__init__()

    def get_index(self):
        return 3


class NOP(Instruction):
    code = 0x00
    name = 'nop'

    def __init__(self):
        super(NOP, self).__init__()

    def execute(self, frame):
        pass


# impdep1 impdep2 breakpoint 为保留操作符
class Impdep1(Instruction):
    code = 0xfe
    name = 'impdep1'

    def __init__(self):
        super(Impdep1, self).__init__()

    def execute(self, frame):
        pass


class Impdep2(Instruction):
    code = 0xff
    name = 'impdep2'

    def __init__(self):
        super(Impdep2, self).__init__()

    def execute(self, frame):
        pass


class Breakpoint(Instruction):
    code = 0xca
    name = 'breakpoint'

    def __init__(self):
        super(Breakpoint, self).__init__()

    def execute(self, frame):
        pass


class RETURN(Instruction):
    code = 0xb1
    name = 'return'
    
    def __init__(self):
        super(RETURN, self).__init__()

    def execute(self, frame):
        frame.thread.pop_frame()


instruction_cache = dict()


def register_instruction(ins):
    instruction_cache[ins.code] = ins

register_instruction(NOP())
register_instruction(IADD())
register_instruction(ICONST_M1())
register_instruction(ICONST_0())
register_instruction(ICONST_1())
register_instruction(ICONST_2())
register_instruction(ICONST_3())
register_instruction(ICONST_4())
register_instruction(ICONST_5())
register_instruction(ILOAD_0())
register_instruction(ILOAD_1())
register_instruction(ISTORE())
register_instruction(ISTORE_0())
register_instruction(ISTORE_1())
register_instruction(ISTORE_2())
register_instruction(ISTORE_3())
register_instruction(INVOKESPECIAL())
register_instruction(INVOKESTATIC())
register_instruction(IRETURN())
register_instruction(RETURN())


# 做个 cache
def get_instruction(code):
    if code in instruction_cache:
        return instruction_cache[code]
    return NOP()
