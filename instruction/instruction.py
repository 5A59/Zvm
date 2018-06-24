# coding=utf-8

import abc
import ctypes
import struct

from runtime.thread import Frame, LocalVars
from runtime.jclass import ClassLoader, JString, JDouble, JLong, JClass, JFloat, JInteger
from runtime.jobject import JObject, JArray, JRef
from base.utils import print_utils, common_utils, error_handler
from interpreter.code_parser import CodeParser
from jthread.jthread import JThread

'''
以下指令没有测试
wide
dup2
dup_x1
dup_x2
dup2_x1
dup2_x2
pop2
if_xxx
swap
'''

'''
未实现指令
jsr
ret
invokeinterface	
monitorenter
monitorexit
multianewarray
jsr_w
breakpoint
impdep1
impdep2
'''


class InsUtils(object):
    TYPE_INT = 1
    TYPE_FLOAT = 2
    TYPE_LONG = 3
    TYPE_DOUBLE = 4
    TYPE_REF = 5
    TYPE_ARRAY = 6
    TYPE_UNKNOWN = -1

    @staticmethod
    def get_type_by_descriptor(desc):
        if desc == 'I' or desc == 'B' or desc == 'C' or desc == 'S' or desc == 'Z':
            return InsUtils.TYPE_INT
        elif desc == 'F':
            return InsUtils.TYPE_FLOAT
        elif desc == 'J':
            return InsUtils.TYPE_LONG
        elif desc == 'D':
            return InsUtils.TYPE_DOUBLE
        elif desc[0] == 'L':
            return InsUtils.TYPE_REF
        elif desc[0] == '[':
            return InsUtils.TYPE_ARRAY
        else:
            return InsUtils.TYPE_UNKNOWN

    @staticmethod
    def check_ref_null(ref):
        if JRef.check_null(ref):
            error_handler.rise_null_point_error()


class Instruction(object):
    code = None  # 字节码
    name = None  # 助记符

    def read_operands(self, code_parser):
        pass

    def execute_wrapper(self, frame):
        hex_code = '%x' % self.code
        print_utils.print_jvm_status('execute ins: ' + self.name + '  ' + hex_code + '   ' + str(frame) + '\n')
        self.execute(frame)

    @abc.abstractmethod
    def execute(self, frame):
        pass


# 不是真正的指令集，但是有和指令差不多的功能
class INNER_INS(Instruction):
    code = -1
    name = 'inner_ins'


class INNER_INVOKE_C_INIT(INNER_INS):
    def __init__(self, jclass):
        super(INNER_INVOKE_C_INIT, self).__init__()
        self.jclass = jclass

    def execute(self, frame):
        method = None
        for m in self.jclass.methods:
            if m.name == '<clinit>':
                method = m
                break
        if method is not None:
            n_frame = Frame(frame.thread, method)
            frame.thread.add_frame(n_frame)
            frame.pc = frame.thread.pc


class ACONST_NULL(Instruction):
    code = 0x1
    name = 'aconst_null'

    def execute(self, frame):
        frame.operand_stack.push(None)


class ALOAD(Instruction):
    code = 0x19
    name = 'aload'

    def __init__(self):
        super(ALOAD, self).__init__()
        self.index = -1

    def read_operands(self, code_parser):
        self.index = code_parser.read_op()

    def execute(self, frame):
        ref = frame.local_vars.get_ref(self.index)
        frame.operand_stack.push_ref(ref)


class ALOAD_N(Instruction):
    @abc.abstractmethod
    def get_index(self):
        pass

    def execute(self, frame):
        ref = frame.local_vars.get_ref(self.get_index())
        frame.operand_stack.push_ref(ref)


class ALOAD_0(ALOAD_N):
    code = 0x2a
    name = 'aload_0'

    def get_index(self):
        return 0


class ALOAD_1(ALOAD_N):
    code = 0x2b
    name = 'aload_1'

    def get_index(self):
        return 1


class ALOAD_2(ALOAD_N):
    code = 0x2c
    name = 'aload_2'

    def get_index(self):
        return 2


class ALOAD_3(ALOAD_N):
    code = 0x2d
    name = 'aload_3'

    def get_index(self):
        return 3


class ARETURN(Instruction):
    code = 0xb0
    name = 'areturn'

    def execute(self, frame):
        frame.thread.pop_frame()
        r_value = frame.operand_stack.pop_ref()
        c_frame = frame.thread.top_frame()
        c_frame.operand_stack.push_ref(r_value)


class ASTORE(Instruction):
    code = 0x3a
    name = 'astore'

    def __init__(self):
        super(ASTORE, self).__init__()
        self.index = -1

    def read_operands(self, code_parser):
        self.index = code_parser.read_op()

    def execute(self, frame):
        ref = frame.operand_stack.pop_ref()
        frame.local_vars.add_ref(self.index, ref)


class ASTORE_N(Instruction):
    @abc.abstractmethod
    def get_index(self):
        pass

    def execute(self, frame):
        ref = frame.operand_stack.pop_ref()
        frame.local_vars.add_ref(self.get_index(), ref)


class ASTORE_0(ASTORE_N):
    code = 0x4b
    name = 'astore_0'

    def get_index(self):
        return 0


class ASTORE_1(ASTORE_N):
    code = 0x4c
    name = 'astore_1'

    def get_index(self):
        return 1


class ASTORE_2(ASTORE_N):
    code = 0x4d
    name = 'astore_2'

    def get_index(self):
        return 2


class ASTORE_3(ASTORE_N):
    code = 0x4e
    name = 'astore_3'

    def get_index(self):
        return 3


class BIPUSH(Instruction):
    code = 0x10
    name = 'bipush'

    def __init__(self):
        super(BIPUSH, self).__init__()
        self.byte = 0

    def read_operands(self, code_parser):
        self.byte = code_parser.read_op()

    def execute(self, frame):
        frame.operand_stack.push_int(ctypes.c_byte(self.byte).value)


class DUP(Instruction):
    code = 0x59
    name = 'dup'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        value = operand_stack.top()
        if isinstance(value, JRef):
            value = value.clone()
        operand_stack.push(value)


class DUP_X1(Instruction):
    code = 0x5a
    name = 'dup_x1'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        value1 = operand_stack.top()
        value2 = operand_stack.top(2)
        if isinstance(value1, JRef):
            value1 = value1.clone()
        if isinstance(value2, JRef):
            value1 = value2.clone()
        operand_stack.push(value2)
        operand_stack.push(value1)


class DUP_X2(Instruction):
    code = 0x5b
    name = 'dup_x2'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        value1 = operand_stack.top()
        value2 = operand_stack.top(2)
        if operand_stack.is_top_type1(2):
            if isinstance(value1, JRef):
                value1 = value1.clone()
            operand_stack.push(value2)
            operand_stack.push(value1)
        else:
            value3 = operand_stack.top(3)
            if isinstance(value1, JRef):
                value1 = value1.clone()
            if isinstance(value2, JRef):
                value1 = value2.clone()
            if isinstance(value3, JRef):
                value1 = value3.clone()
            operand_stack.push(value3)
            operand_stack.push(value2)
            operand_stack.push(value1)


class DUP2(Instruction):
    code = 0x5c
    name = 'dup2'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        value = operand_stack.top()
        if operand_stack.is_top_type1():
            operand_stack.push(value)
            return

        value2 = operand_stack.top(2)
        if isinstance(value, JRef):
            value = value.clone()
        if isinstance(value2, JRef):
            value = value.clone()
        operand_stack.push(value2)
        operand_stack.push(value)


class DUP2_X1(Instruction):
    code = 0x5d
    name = 'dup2_x1'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        value1 = operand_stack.top()
        value2 = operand_stack.top(2)
        if operand_stack.is_top_type1():
            if isinstance(value2, JRef):
                value1 = value2.clone()
            operand_stack.push(value2)
            operand_stack.push(value1)
        else:
            value3 = operand_stack.top(3)
            if isinstance(value1, JRef):
                value1 = value1.clone()
            if isinstance(value2, JRef):
                value1 = value2.clone()
            if isinstance(value3, JRef):
                value1 = value3.clone()
            operand_stack.push(value3)
            operand_stack.push(value2)
            operand_stack.push(value1)


class DUP2_X2(Instruction):
    code = 0x5e
    name = 'dup2_x2'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        value1 = operand_stack.top()
        value2 = operand_stack.top(2)
        value3 = operand_stack.top(3)
        if operand_stack.is_top_type1() or operand_stack.is_top_type1(2) or operand_stack.is_top_type1(3):
            if isinstance(value1, JRef):
                value1 = value1.clone()
            if isinstance(value2, JRef):
                value1 = value2.clone()
            if isinstance(value3, JRef):
                value1 = value3.clone()
            operand_stack.push(value3)
            operand_stack.push(value2)
            operand_stack.push(value1)
        else:
            value4 = operand_stack.top(4)
            if isinstance(value1, JRef):
                value1 = value1.clone()
            if isinstance(value2, JRef):
                value1 = value2.clone()
            if isinstance(value3, JRef):
                value1 = value3.clone()
            if isinstance(value4, JRef):
                value1 = value4.clone()
            operand_stack.push(value4)
            operand_stack.push(value3)
            operand_stack.push(value2)
            operand_stack.push(value1)


class PUTSTATIC(Instruction):
    code = 0xb3
    name = 'putstatic'

    def __init__(self):
        super(PUTSTATIC, self).__init__()
        self.index = -1

    def read_operands(self, code_parser):
        index1 = code_parser.read_op()
        index2 = code_parser.read_op()
        self.index = (index1 << 8) | index2

    def execute(self, frame):
        constant_pool = frame.method.jclass.constant_pool
        ref = constant_pool.constants[self.index]
        ref.resolve_field(frame.method.jclass.class_loader)
        ftype = InsUtils.get_type_by_descriptor(ref.descriptor)
        jclass = ref.cache_class
        if not jclass.has_inited:
            c_init = INNER_INVOKE_C_INIT(jclass)
            c_init.execute(frame)
            jclass.has_inited = True
            return
        slots = jclass.static_fields
        slot = slots[ref.field.name]
        operand_stack = frame.operand_stack
        if ftype == InsUtils.TYPE_INT:
            slot.num = operand_stack.pop_int()
        elif ftype == InsUtils.TYPE_FLOAT:
            slot.num = operand_stack.pop_float()
        elif ftype == InsUtils.TYPE_LONG:
            slot.num = operand_stack.pop_long()
        elif ftype == InsUtils.TYPE_DOUBLE:
            slot.num = operand_stack.pop_double()
        else:
            slot.ref = operand_stack.pop_ref()


class GETSTATIC(Instruction):
    code = 0xb2
    name = 'getstatic'

    def __init__(self):
        super(GETSTATIC, self).__init__()
        self.index = -1

    def read_operands(self, code_parser):
        index1 = code_parser.read_op()
        index2 = code_parser.read_op()
        self.index = (index1 << 8) | index2

    def execute(self, frame):
        constant_pool = frame.method.jclass.constant_pool
        ref = constant_pool.constants[self.index]
        ref.resolve_field(frame.method.jclass.class_loader)
        ftype = InsUtils.get_type_by_descriptor(ref.descriptor)
        jclass = ref.cache_class
        if not jclass.has_inited:
            c_init = INNER_INVOKE_C_INIT(jclass)
            c_init.execute(frame)
            jclass.has_inited = True
            return
        slots = jclass.static_fields
        val = slots[ref.field.name]
        if val is not None:
            if val.num is not None:
                if ftype == InsUtils.TYPE_INT:
                    frame.operand_stack.push_int(val.num)
                elif ftype == InsUtils.TYPE_FLOAT:
                    frame.operand_stack.push_float(val.num)
                elif ftype == InsUtils.TYPE_LONG:
                    frame.operand_stack.push_long(val.num)
                elif ftype == InsUtils.TYPE_DOUBLE:
                    frame.operand_stack.push_double(val.num)
            elif val.ref is not None:
                frame.operand_stack.push_ref(val.ref)
            else:
                frame.operand_stack.push(None)
        else:
            frame.operand_stack.push(None)


class JUMP_INC(Instruction):
    def jump_by(self, frame, offset):
        frame.pc = frame.thread.pc + offset

    def jump_to(self, frame, pc):
        frame.pc = pc


class GOTO(JUMP_INC):
    code = 0xa7
    name = 'goto'

    def __init__(self):
        super(GOTO, self).__init__()
        self.branch = 0

    def read_operands(self, code_parser):
        branch1 = code_parser.read_op()
        branch2 = code_parser.read_op()
        self.branch = common_utils.get_short_from_bytes(branch1, branch2)

    def execute(self, frame):
        self.jump_by(frame, self.branch)


class GOTO_W(JUMP_INC):
    code = 0xc8
    name = 'goto_w'

    def __init__(self):
        super(GOTO_W, self).__init__()
        self.branch = 0

    def read_operands(self, code_parser):
        branch1 = code_parser.read_op()
        branch2 = code_parser.read_op()
        branch3 = code_parser.read_op()
        branch4 = code_parser.read_op()
        self.branch = (branch1 << 24) | (branch2 << 16) | (branch3 << 8) | branch4

    def execute(self, frame):
        self.jump_by(frame, self.branch)


class IASTORE(Instruction):
    code = 0x4f
    name = 'iastore'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        value = operand_stack.pop_int()
        index = operand_stack.pop_int()
        aref = operand_stack.pop_ref()
        InsUtils.check_ref_null(aref)
        aref.handler.obj.add_item(index, value)


class IALOAD(Instruction):
    code = 0x2e
    name = 'iaload'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        index = operand_stack.pop_int()
        aref = operand_stack.pop_ref()
        InsUtils.check_ref_null(aref)
        val = aref.handler.obj.get_item(index)
        operand_stack.push_int(val)


class CASTORE(Instruction):
    code = 0x55
    name = 'castore'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        value = operand_stack.pop_int()
        index = operand_stack.pop_int()
        aref = operand_stack.pop_ref()
        InsUtils.check_ref_null(aref)
        aref.handler.obj.add_item(index, value)


class CALOAD(Instruction):
    code = 0x34
    name = 'caload'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        index = operand_stack.pop_int()
        aref = operand_stack.pop_ref()
        InsUtils.check_ref_null(aref)
        val = aref.handler.obj.get_item(index)
        operand_stack.push_int(val)


class DASTORE(Instruction):
    code = 0x52
    name = 'dastore'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        value = operand_stack.pop_double()
        index = operand_stack.pop_int()
        aref = operand_stack.pop_ref()
        InsUtils.check_ref_null(aref)
        aref.handler.obj.add_item(index, value)


class DALOAD(Instruction):
    code = 0x31
    name = 'daload'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        index = operand_stack.pop_int()
        aref = operand_stack.pop_ref()
        InsUtils.check_ref_null(aref)
        val = aref.handler.obj.get_item(index)
        operand_stack.push_double(val)


class FASTORE(Instruction):
    code = 0x51
    name = 'fastore'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        value = operand_stack.pop_float()
        index = operand_stack.pop_int()
        aref = operand_stack.pop_ref()
        InsUtils.check_ref_null(aref)
        aref.handler.obj.add_item(index, value)


class FALOAD(Instruction):
    code = 0x30
    name = 'faload'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        index = operand_stack.pop_int()
        aref = operand_stack.pop_ref()
        InsUtils.check_ref_null(aref)
        val = aref.handler.obj.get_item(index)
        operand_stack.push_float(val)


class LASTORE(Instruction):
    code = 0x50
    name = 'lastore'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        value = operand_stack.pop_long()
        index = operand_stack.pop_int()
        aref = operand_stack.pop_ref()
        InsUtils.check_ref_null(aref)
        aref.handler.obj.add_item(index, value)


class LALOAD(Instruction):
    code = 0x2f
    name = 'laload'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        index = operand_stack.pop_int()
        aref = operand_stack.pop_ref()
        InsUtils.check_ref_null(aref)
        val = aref.handler.obj.get_item(index)
        operand_stack.push_long(val)


class SASTORE(Instruction):
    code = 0x56
    name = 'sastore'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        value = operand_stack.pop_int()
        index = operand_stack.pop_int()
        aref = operand_stack.pop_ref()
        InsUtils.check_ref_null(aref)
        aref.handler.obj.add_item(index, value)


class SALOAD(Instruction):
    code = 0x35
    name = 'saload'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        index = operand_stack.pop_int()
        aref = operand_stack.pop_ref()
        InsUtils.check_ref_null(aref)
        val = aref.handler.obj.get_item(index)
        operand_stack.push_int(val)


class AASTORE(Instruction):
    code = 0x53
    name = 'aastore'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        value = operand_stack.pop_ref()
        index = operand_stack.pop_int()
        aref = operand_stack.pop_ref()
        InsUtils.check_ref_null(aref)
        aref.handler.obj.add_ref_item(index, value)


class AALOAD(Instruction):
    code = 0x32
    name = 'aaload'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        index = operand_stack.pop_int()
        aref = operand_stack.pop_ref()
        InsUtils.check_ref_null(aref)
        val = aref.handler.obj.get_item(index)
        operand_stack.push_ref(val)


class BASTORE(Instruction):
    code = 0x54
    name = 'bastore'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        value = operand_stack.pop_int()
        index = operand_stack.pop_int()
        aref = operand_stack.pop_ref()
        InsUtils.check_ref_null(aref)
        aref.handler.obj.add_item(index, value)


class BALOAD(Instruction):
    code = 0x33
    name = 'baload'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        index = operand_stack.pop_int()
        aref = operand_stack.pop_ref()
        InsUtils.check_ref_null(aref)
        val = aref.handler.obj.get_item(index)
        operand_stack.push_int(val)


class IINC(Instruction):
    code = 0x84
    name = 'iinc'

    def __init__(self):
        super(IINC, self).__init__()
        self.index = 0
        self.const = 0

    def read_operands(self, code_parser):
        self.index = code_parser.read_op()
        self.const = code_parser.read_op()

    def execute(self, frame):
        val = frame.local_vars.get_int(self.index)
        val += self.const
        frame.local_vars.add_int(self.index, val)


class I2L(Instruction):
    code = 0x85
    name = 'i2l'

    def execute(self, frame):
        val = frame.operand_stack.pop_int()
        frame.operand_stack.push_long(val)


class I2F(Instruction):
    code = 0x86
    name = 'i2f'

    def execute(self, frame):
        val = frame.operand_stack.pop_int()
        frame.operand_stack.push_float(ctypes.c_float(val).value)


class I2D(Instruction):
    code = 0x87
    name = 'i2d'

    def execute(self, frame):
        val = frame.operand_stack.pop_int()
        frame.operand_stack.push_double(ctypes.c_double(val).value)


class L2I(Instruction):
    code = 0x88
    name = 'l2i'

    def execute(self, frame):
        val = frame.operand_stack.pop_long()
        frame.operand_stack.push_int(ctypes.c_int32(val).value)


class L2F(Instruction):
    code = 0x89
    name = 'l2f'

    def execute(self, frame):
        val = frame.operand_stack.pop_long()
        frame.operand_stack.push_float(ctypes.c_float(val).value)


class L2D(Instruction):
    code = 0x8a
    name = 'l2d'

    def execute(self, frame):
        val = frame.operand_stack.pop_long()
        frame.operand_stack.push_double(ctypes.c_double(val).value)


class F2I(Instruction):
    code = 0x8b
    name = 'f2i'

    def execute(self, frame):
        val = frame.operand_stack.pop_float()
        frame.operand_stack.push_int(ctypes.c_int32(val).value)


class F2L(Instruction):
    code = 0x8c
    name = 'f2l'

    def execute(self, frame):
        val = frame.operand_stack.pop_float()
        frame.operand_stack.push_long(ctypes.c_long(val).value)


class F2D(Instruction):
    code = 0x8d
    name = 'f2d'

    def execute(self, frame):
        val = frame.operand_stack.pop_float()
        frame.operand_stack.push_double(ctypes.c_double(val).value)


class D2I(Instruction):
    code = 0x8e
    name = 'd2i'

    def execute(self, frame):
        val = frame.operand_stack.pop_double()
        frame.operand_stack.push_int(ctypes.c_int32(val).value)


class D2L(Instruction):
    code = 0x8f
    name = 'd2l'

    def execute(self, frame):
        val = frame.operand_stack.pop_double()
        frame.operand_stack.push_long(ctypes.c_long(val).value)


class D2F(Instruction):
    code = 0x90
    name = 'd2f'

    def execute(self, frame):
        val = frame.operand_stack.pop_double()
        frame.operand_stack.push_float(ctypes.c_float(val).value)


class I2B(Instruction):
    code = 0x91
    name = 'i2b'

    def execute(self, frame):
        val = frame.operand_stack.pop_int()
        frame.operand_stack.push_int(ctypes.c_byte(val).value)


class I2C(Instruction):
    code = 0x92
    name = 'i2c'

    def execute(self, frame):
        val = frame.operand_stack.pop_int()
        frame.operand_stack.push_int(ctypes.c_char(val).value)


class I2S(Instruction):
    code = 0x93
    name = 'i2s'

    def execute(self, frame):
        val = frame.operand_stack.pop_int()
        frame.operand_stack.push_int(ctypes.c_short(val).value)


class LCMP(Instruction):
    code = 0x94
    name = 'lcmp'

    def execute(self, frame):
        value2 = frame.operand_stack.pop_long()
        value1 = frame.operand_stack.pop_long()
        if value1 > value2:
            frame.operand_stack.push_int(1)
        elif value1 < value2:
            frame.operand_stack.push_int(-1)
        else:
            frame.operand_stack.push_int(0)


class FCMPOP(Instruction):
    # TODO: 对 fcmpl 和 fcmpd 没有做区分
    def execute(self, frame):
        value2 = frame.operand_stack.pop_float()
        value1 = frame.operand_stack.pop_float()
        if value1 > value2:
            frame.operand_stack.push_int(1)
        elif value1 < value2:
            frame.operand_stack.push_int(-1)
        else:
            frame.operand_stack.push_int(0)


class FCMPL(FCMPOP):
    code = 0x95
    name = 'fcmpl'


class FCMPD(FCMPOP):
    code = 0x96
    name = 'fcmpd'


class DCMPOP(Instruction):
    # TODO: 对 dcmpl 和 dcmpd 没有做区分
    def execute(self, frame):
        value2 = frame.operand_stack.pop_double()
        value1 = frame.operand_stack.pop_double()
        if value1 > value2:
            frame.operand_stack.push_int(1)
        elif value1 < value2:
            frame.operand_stack.push_int(-1)
        else:
            frame.operand_stack.push_int(0)


class DCMPL(DCMPOP):
    code = 0x97
    name = 'dcmpl'


class DCMPD(FCMPOP):
    code = 0x98
    name = 'dcmpd'


class ICONST_I(Instruction):
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

    def get_index(self):
        return -1


class ICONST_0(ICONST_I):
    code = 0x3
    name = 'iconst_0'

    def get_index(self):
        return 0


class ICONST_1(ICONST_I):
    code = 0x4
    name = 'iconst_1'

    def get_index(self):
        return 1


class ICONST_2(ICONST_I):
    code = 0x5
    name = 'iconst_2'

    def get_index(self):
        return 2


class ICONST_3(ICONST_I):
    code = 0x6
    name = 'iconst_3'

    def get_index(self):
        return 3


class ICONST_4(ICONST_I):
    code = 0x7
    name = 'iconst_4'

    def get_index(self):
        return 4


class ICONST_5(ICONST_I):
    code = 0x8
    name = 'iconst_5'

    def get_index(self):
        return 5


class LCONST_L(Instruction):
    @abc.abstractmethod
    def get_index(self):
        pass

    def execute(self, frame):
        index = self.get_index()
        stack = frame.operand_stack
        stack.push_long(index)


class LCONST_0(LCONST_L):
    code = 0x9
    name = 'lconst_0'

    def get_index(self):
        return 0


class LCONST_1(LCONST_L):
    code = 0xa
    name = 'lconst_1'

    def get_index(self):
        return 1


class FCONST_L(Instruction):
    @abc.abstractmethod
    def get_index(self):
        pass

    def execute(self, frame):
        index = self.get_index()
        stack = frame.operand_stack
        stack.push_float(index)


class FCONST_0(FCONST_L):
    code = 0xb
    name = 'fconst_0'

    def get_index(self):
        return 0.0


class FCONST_1(FCONST_L):
    code = 0xc
    name = 'fconst_1'

    def get_index(self):
        return 1.0


class FCONST_2(FCONST_L):
    code = 0xd
    name = 'fconst_2'

    def get_index(self):
        return 2.0


class DCONST_L(Instruction):
    @abc.abstractmethod
    def get_index(self):
        pass

    def execute(self, frame):
        index = self.get_index()
        stack = frame.operand_stack
        stack.push_double(index)


class DCONST_0(FCONST_L):
    code = 0xe
    name = 'dconst_0'

    def get_index(self):
        return 0.0


class DCONST_1(FCONST_L):
    code = 0xf
    name = 'dconst_1'

    def get_index(self):
        return 1.0


class ILOAD(Instruction):
    code = 0x15
    name = 'iload'

    def __init__(self):
        super(ILOAD, self).__init__()
        self.index = 0

    def read_operands(self, code_parser):
        self.index = code_parser.read_op()

    def execute(self, frame):
        local_vars = frame.local_vars
        operand_stack = frame.operand_stack
        value = local_vars.get_int(self.index)
        operand_stack.push_int(value)


class ILOAD_N(Instruction):
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

    def get_index(self):
        return 0


class ILOAD_1(ILOAD_N):
    code = 0x1b
    name = 'iload_1'

    def get_index(self):
        return 1


class ILOAD_2(ILOAD_N):
    code = 0x1c
    name = 'iload_2'

    def get_index(self):
        return 2


class ILOAD_3(ILOAD_N):
    code = 0x1d
    name = 'iload_3'

    def get_index(self):
        return 3


class DLOAD_N(Instruction):
    @abc.abstractmethod
    def get_index(self):
        pass

    def execute(self, frame):
        index = self.get_index()
        local_vars = frame.local_vars
        operand_stack = frame.operand_stack
        value = local_vars.get_double(index)
        operand_stack.push_double(value)


class DLOAD(DLOAD_N):
    code = 0x18
    name = 'dload'

    def __init__(self):
        super(DLOAD, self).__init__()
        self.index = 0

    def read_operands(self, code_parser):
        self.index = code_parser.read_op()

    def get_index(self):
        return self.index


class DLOAD_0(DLOAD_N):
    code = 0x26
    name = 'dload_0'

    def get_index(self):
        return 0


class DLOAD_1(DLOAD_N):
    code = 0x27
    name = 'dload_1'

    def get_index(self):
        return 1


class DLOAD_2(DLOAD_N):
    code = 0x28
    name = 'dload_2'

    def get_index(self):
        return 2


class DLOAD_3(DLOAD_N):
    code = 0x29
    name = 'dload_3'

    def get_index(self):
        return 3


class FLOAD_N(Instruction):
    @abc.abstractmethod
    def get_index(self):
        pass

    def execute(self, frame):
        index = self.get_index()
        local_vars = frame.local_vars
        operand_stack = frame.operand_stack
        value = local_vars.get_float(index)
        operand_stack.push_float(value)


class FLOAD(FLOAD_N):
    code = 0x17
    name = 'fload'

    def __init__(self):
        super(FLOAD, self).__init__()
        self.index = 0

    def read_operands(self, code_parser):
        self.index = code_parser.read_op()

    def get_index(self):
        return self.index


class FLOAD_0(FLOAD_N):
    code = 0x22
    name = 'fload_0'

    def get_index(self):
        return 0


class FLOAD_1(FLOAD_N):
    code = 0x23
    name = 'fload_1'

    def get_index(self):
        return 1


class FLOAD_2(FLOAD_N):
    code = 0x24
    name = 'fload_2'

    def get_index(self):
        return 2


class FLOAD_3(FLOAD_N):
    code = 0x25
    name = 'fload_3'

    def get_index(self):
        return 3


class LLOAD_N(Instruction):
    @abc.abstractmethod
    def get_index(self):
        pass

    def execute(self, frame):
        index = self.get_index()
        local_vars = frame.local_vars
        operand_stack = frame.operand_stack
        value = local_vars.get_long(index)
        operand_stack.push_long(value)


class LLOAD(LLOAD_N):
    code = 0x16
    name = 'lload'

    def __init__(self):
        super(LLOAD, self).__init__()
        self.index = 0

    def read_operands(self, code_parser):
        self.index = code_parser.read_op()

    def get_index(self):
        return self.index


class LLOAD_0(LLOAD_N):
    code = 0x1e
    name = 'lload_0'

    def get_index(self):
        return 0


class LLOAD_1(LLOAD_N):
    code = 0x1f
    name = 'lload_1'

    def get_index(self):
        return 1


class LLOAD_2(LLOAD_N):
    code = 0x20
    name = 'lload_2'

    def get_index(self):
        return 2


class LLOAD_3(LLOAD_N):
    code = 0x21
    name = 'lload_3'

    def get_index(self):
        return 3


class IADD(Instruction):
    code = 0x60
    name = 'iadd'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        val1 = operand_stack.pop_int()
        val2 = operand_stack.pop_int()
        res = val1 + val2
        operand_stack.push_int(res)


class LADD(Instruction):
    code = 0x61
    name = 'ladd'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        val1 = operand_stack.pop_long()
        val2 = operand_stack.pop_long()
        res = val1 + val2
        operand_stack.push_long(res)


class FADD(Instruction):
    code = 0x62
    name = 'fadd'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        val1 = operand_stack.pop_float()
        val2 = operand_stack.pop_float()
        res = val1 + val2
        operand_stack.push_float(res)


class DADD(Instruction):
    code = 0x63
    name = 'dadd'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        val1 = operand_stack.pop_double()
        val2 = operand_stack.pop_double()
        res = val1 + val2
        operand_stack.push_double(res)


class ISUB(Instruction):
    code = 0x64
    name = 'isub'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        val1 = operand_stack.pop_int()
        val2 = operand_stack.pop_int()
        res = val1 - val2
        operand_stack.push_int(res)


class LSUB(Instruction):
    code = 0x65
    name = 'lsub'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        val1 = operand_stack.pop_long()
        val2 = operand_stack.pop_long()
        res = val1 - val2
        operand_stack.push_long(res)


class FSUB(Instruction):
    code = 0x66
    name = 'fsub'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        val1 = operand_stack.pop_float()
        val2 = operand_stack.pop_float()
        res = val1 - val2
        operand_stack.push_float(res)


class DSUB(Instruction):
    code = 0x67
    name = 'dsub'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        val1 = operand_stack.pop_double()
        val2 = operand_stack.pop_double()
        res = val1 - val2
        operand_stack.push_double(res)


class IMUL(Instruction):
    code = 0x68
    name = 'imul'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        val1 = operand_stack.pop_int()
        val2 = operand_stack.pop_int()
        res = val1 * val2
        operand_stack.push_int(res)


class LMUL(Instruction):
    code = 0x69
    name = 'lmul'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        val1 = operand_stack.pop_long()
        val2 = operand_stack.pop_long()
        res = val1 * val2
        operand_stack.push_long(res)


class FMUL(Instruction):
    code = 0x6a
    name = 'fmul'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        val1 = operand_stack.pop_float()
        val2 = operand_stack.pop_float()
        res = val1 * val2
        operand_stack.push_float(res)


class DMUL(Instruction):
    code = 0x6b
    name = 'dmul'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        val1 = operand_stack.pop_double()
        val2 = operand_stack.pop_double()
        res = val1 * val2
        operand_stack.push_double(res)


class IDIV(Instruction):
    code = 0x6c
    name = 'idiv'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        val1 = operand_stack.pop_int()
        val2 = operand_stack.pop_int()
        if val2 == 0:
            error_handler.rise_runtime_error('java.lang.ArithmeticException: x / 0')
        res = val1 / val2
        operand_stack.push_int(res)


class LDIV(Instruction):
    code = 0x6d
    name = 'ldiv'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        val1 = operand_stack.pop_long()
        val2 = operand_stack.pop_long()
        if val2 == 0:
            error_handler.rise_runtime_error('java.lang.ArithmeticException: x / 0')
        res = val1 / val2
        operand_stack.push_long(res)


class FDIV(Instruction):
    code = 0x6e
    name = 'fdiv'

    def execute(self, frame):
        # TODO: IEEE 规范中规定的运算规则
        operand_stack = frame.operand_stack
        val1 = operand_stack.pop_float()
        val2 = operand_stack.pop_float()
        res = val1 / val2
        operand_stack.push_float(res)


class DDIV(Instruction):
    code = 0x6f
    name = 'ddiv'

    def execute(self, frame):
        # TODO: IEEE 规范中规定的运算规则
        operand_stack = frame.operand_stack
        val1 = operand_stack.pop_double()
        val2 = operand_stack.pop_double()
        res = val1 / val2
        operand_stack.push_double(res)


class IREM(Instruction):
    code = 0x70
    name = 'irem'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        val2 = operand_stack.pop_int()
        val1 = operand_stack.pop_int()
        if val2 == 0:
            error_handler.rise_runtime_error('java.lang.ArithmeticException: x / 0')
        # res = val1 - int(val1 / val2) * val2
        res = val1 % val2
        operand_stack.push_int(res)


class LREM(Instruction):
    code = 0x71
    name = 'lrem'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        val2 = operand_stack.pop_long()
        val1 = operand_stack.pop_long()
        if val2 == 0:
            error_handler.rise_runtime_error('java.lang.ArithmeticException: x / 0')
        # res = val1 - int(val1 / val2) * val2
        res = val1 % val2
        operand_stack.push_long(res)


class FREM(Instruction):
    code = 0x72
    name = 'frem'

    def execute(self, frame):
        # TODO: IEEE 规范中规定的运算规则
        operand_stack = frame.operand_stack
        val2 = operand_stack.pop_float()
        val1 = operand_stack.pop_float()
        res = val1 % val2
        operand_stack.push_float(res)


class DREM(Instruction):
    code = 0x73
    name = 'drem'

    def execute(self, frame):
        # TODO: IEEE 规范中规定的运算规则
        operand_stack = frame.operand_stack
        val2 = operand_stack.pop_double()
        val1 = operand_stack.pop_double()
        res = val1 % val2
        operand_stack.push_double(res)


class INEG(Instruction):
    code = 0x74
    name = 'ineg'

    def execute(self, frame):
        val = frame.operand_stack.pop_int()
        frame.operand_stack.push_int(-val)


class LNEG(Instruction):
    code = 0x75
    name = 'lneg'

    def execute(self, frame):
        val = frame.operand_stack.pop_long()
        frame.operand_stack.push_long(-val)


class FNEG(Instruction):
    code = 0x76
    name = 'fneg'

    def execute(self, frame):
        val = frame.operand_stack.pop_float()
        frame.operand_stack.push_float(-val)


class DNEG(Instruction):
    code = 0x77
    name = 'dneg'

    def execute(self, frame):
        val = frame.operand_stack.pop_double()
        frame.operand_stack.push_double(-val)


class ISHL(Instruction):
    code = 0x78
    name = 'ishl'

    def execute(self, frame):
        val2 = frame.operand_stack.pop_int()
        val1 = frame.operand_stack.pop_int()
        s = val2 & 0x1f
        res = val1 << s
        frame.operand_stack.push_int(res)


class LSHL(Instruction):
    code = 0x79
    name = 'lshl'

    def execute(self, frame):
        val2 = frame.operand_stack.pop_long()
        val1 = frame.operand_stack.pop_long()
        s = val2 & 0x3f
        res = val1 << s
        frame.operand_stack.push_long(res)


class ISHR(Instruction):
    code = 0x7a
    name = 'ishr'

    def execute(self, frame):
        val2 = frame.operand_stack.pop_int()
        val1 = frame.operand_stack.pop_int()
        s = val2 & 0x1f
        res = val1 >> s
        frame.operand_stack.push_int(res)


class LSHR(Instruction):
    code = 0x7b
    name = 'lshr'

    def execute(self, frame):
        val2 = frame.operand_stack.pop_long()
        val1 = frame.operand_stack.pop_long()
        s = val2 & 0x3f
        res = val1 >> s
        frame.operand_stack.push_long(res)


class IUSHR(Instruction):
    code = 0x7c
    name = 'iushr'

    def execute(self, frame):
        val2 = frame.operand_stack.pop_int()
        val1 = frame.operand_stack.pop_int()
        s = val2 & 0x1f
        val = ctypes.c_uint32(val1).value
        res = ctypes.c_int32(val >> s).value
        frame.operand_stack.push_int(res)


class LUSHR(Instruction):
    code = 0x7d
    name = 'lushr'

    def execute(self, frame):
        val2 = frame.operand_stack.pop_long()
        val1 = frame.operand_stack.pop_long()
        s = val2 & 0x3f
        val = ctypes.c_uint64(val1).value
        res = ctypes.c_int64(val >> s).value
        frame.operand_stack.push_int(res)


class IAND(Instruction):
    code = 0x7e
    name = 'iand'

    def execute(self, frame):
        val2 = frame.operand_stack.pop_int()
        val1 = frame.operand_stack.pop_int()
        res = val1 & val2
        frame.operand_stack.push_int(res)


class LAND(Instruction):
    code = 0x7f
    name = 'land'

    def execute(self, frame):
        val2 = frame.operand_stack.pop_long()
        val1 = frame.operand_stack.pop_long()
        res = val1 & val2
        frame.operand_stack.push_long(res)


class IOR(Instruction):
    code = 0x80
    name = 'ior'

    def execute(self, frame):
        val2 = frame.operand_stack.pop_int()
        val1 = frame.operand_stack.pop_int()
        res = val1 | val2
        frame.operand_stack.push_int(res)


class LOR(Instruction):
    code = 0x81
    name = 'lor'

    def execute(self, frame):
        val2 = frame.operand_stack.pop_long()
        val1 = frame.operand_stack.pop_long()
        res = val1 | val2
        frame.operand_stack.push_long(res)


class IXOR(Instruction):
    code = 0x82
    name = 'ixor'

    def execute(self, frame):
        val2 = frame.operand_stack.pop_int()
        val1 = frame.operand_stack.pop_int()
        res = val1 ^ val2
        frame.operand_stack.push_int(res)


class LXOR(Instruction):
    code = 0x83
    name = 'lxor'

    def execute(self, frame):
        val2 = frame.operand_stack.pop_long()
        val1 = frame.operand_stack.pop_long()
        res = val1 ^ val2
        frame.operand_stack.push_long(res)


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
        # TODO: 先忽略基础类的所有方法
        if n_method_ref.class_name == 'java/lang/Object':
            return
        print_utils.print_jvm_status('invokespecial: ' + n_method_ref.name)
        n_method = n_method_ref.resolve_method(frame.method.jclass.class_loader)
        n_frame = Frame(frame.thread, n_method)
        frame.thread.add_frame(n_frame)
        arg_desc = n_method.arg_desc
        i = len(arg_desc)
        for arg in arg_desc:
            if arg == 'I' or arg == 'S' or arg == 'Z' or arg == 'C':
                value = frame.operand_stack.pop_int()
                n_frame.local_vars.add_int(i, value)
            elif arg == 'J':
                value = frame.operand_stack.pop_long()
                n_frame.local_vars.add_long(i, value)
            elif arg == 'F':
                value = frame.operand_stack.pop_float()
                n_frame.local_vars.add_float(i, value)
            elif arg == 'D':
                value = frame.operand_stack.pop_double()
                n_frame.local_vars.add_double(i, value)
            elif arg[0] == 'L':
                jref = frame.operand_stack.pop_ref()
                n_frame.local_vars.add_ref(i, jref)
            i -= 1
        n_frame.local_vars.add_ref(0, frame.operand_stack.pop())


class INVOKEVIRTUAL(Instruction):
    code = 0xb6
    name = 'invokevirtual'

    def __init__(self):
        super(INVOKEVIRTUAL, self).__init__()
        self.index = -1

    def read_operands(self, code_parser):
        index1 = code_parser.read_op()
        index2 = code_parser.read_op()
        self.index = (index1 << 8) | index2

    def execute(self, frame):
        # TODO: 方法校验
        constant_pool = frame.method.jclass.constant_pool.constants
        n_method_ref = constant_pool[self.index]
        # TODO: 先忽略基类的所有方法
        if n_method_ref.class_name == 'java/lang/Object':
            return
        print_utils.print_jvm_status('invokevirtual: ' + n_method_ref.name)
        # 主要是为了获取参数个数
        n_method = n_method_ref.resolve_method_with_super(frame.method.jclass.class_loader)
        arg_desc = n_method.arg_desc
        ref = frame.operand_stack.top(len(arg_desc))
        if ref is not None:
            real_class_name = ref.handler.obj.jclass.name
            if n_method_ref.class_name != real_class_name:
                n_method = n_method_ref.re_resolve_method_with_super_by_class_name(frame.method.jclass.class_loader,
                                                                                   real_class_name)
        n_frame = Frame(frame.thread, n_method)
        frame.thread.add_frame(n_frame)
        i = len(arg_desc)
        for arg in arg_desc:
            if arg == 'I' or arg == 'S' or arg == 'Z' or arg == 'C' or arg == 'B':
                value = frame.operand_stack.pop_int()
                n_frame.local_vars.add_int(i, value)
            elif arg == 'J':
                value = frame.operand_stack.pop_long()
                n_frame.local_vars.add_long(i, value)
            elif arg == 'F':
                value = frame.operand_stack.pop_float()
                n_frame.local_vars.add_float(i, value)
            elif arg == 'D':
                value = frame.operand_stack.pop_double()
                n_frame.local_vars.add_double(i, value)
            elif arg[0] == 'L':
                jref = frame.operand_stack.pop_ref()
                n_frame.local_vars.add_ref(i, jref)
            i -= 1
        n_frame.local_vars.add_ref(0, frame.operand_stack.pop())
        self.__hack(n_frame, n_method)

    # 暂时做一些 hack 处理，比如输出
    def __hack(self, n_frame, method):
        # 处理 print
        self.__hack_println(n_frame, method)
        # 处理 thread
        self.__hack_thread(n_frame, method)

    def __hack_thread(self, n_frame, method):
        jthis = n_frame.local_vars.get_ref(0)
        if method.name == 'start' and jthis.handler.obj.jclass.super_class_name == 'java/lang/Thread':
            for m in jthis.handler.obj.jclass.methods:
                if m.name == 'run':
                    JThread.start_new_thread(m)

    def __hack_println(self, n_frame, method):
        if method.name == 'println' and method.jclass.name == 'java/io/PrintStream':
            if method.descriptor == '(Ljava/lang/String;)Ljava/io/PrintStream;':
                jref = n_frame.local_vars.get_ref(1)
                print_utils.StreamPrinter.append_msg(n_frame.thread, jref.data)
            elif method.descriptor == '(I)Ljava/io/PrintStream;':
                jint = n_frame.local_vars.get_int(1)
                print_utils.StreamPrinter.append_msg(n_frame.thread, jint)
            elif method.descriptor == '(S)Ljava/io/PrintStream;':
                jint = n_frame.local_vars.get_int(1)
                print_utils.StreamPrinter.append_msg(n_frame.thread, jint)
            elif method.descriptor == '(B)Ljava/io/PrintStream;':
                jint = n_frame.local_vars.get_int(1)
                print_utils.StreamPrinter.append_msg(n_frame.thread, jint)
            elif method.descriptor == '(C)Ljava/io/PrintStream;':
                jint = n_frame.local_vars.get_int(1)
                print_utils.StreamPrinter.append_msg(n_frame.thread, chr(jint))
            elif method.descriptor == '(J)Ljava/io/PrintStream;':
                jlong = n_frame.local_vars.get_long(1)
                print_utils.StreamPrinter.append_msg(n_frame.thread, jlong)
            elif method.descriptor == '(D)Ljava/io/PrintStream;':
                jdouble = n_frame.local_vars.get_double(1)
                print_utils.StreamPrinter.append_msg(n_frame.thread, jdouble)
            elif method.descriptor == '(F)Ljava/io/PrintStream;':
                jfloat = n_frame.local_vars.get_float(1)
                print_utils.StreamPrinter.append_msg(n_frame.thread, jfloat)
            elif method.descriptor == '(Z)Ljava/io/PrintStream;':
                jint = n_frame.local_vars.get_int(1)
                if jint == 0:  # False
                    print_utils.StreamPrinter.append_msg(n_frame.thread, 'false')
                elif jint == 1:  # True
                    print_utils.StreamPrinter.append_msg(n_frame.thread, 'true')
                else:
                    error_handler.rise_runtime_error('runtime error: boolean not true or false')


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
        print_utils.print_jvm_status('invokestatic: ' + n_method_ref.name)
        n_method = n_method_ref.resolve_method(frame.method.jclass.class_loader)
        n_frame = Frame(frame.thread, n_method)
        frame.thread.add_frame(n_frame)
        arg_desc = n_method.arg_desc
        i = len(arg_desc)
        for arg in arg_desc:
            i -= 1
            if arg == 'I' or arg == 'S' or arg == 'Z' or arg == 'C':
                value = frame.operand_stack.pop_int()
                n_frame.local_vars.add_int(i, value)
            elif arg == 'J':
                value = frame.operand_stack.pop_long()
                n_frame.local_vars.add_long(i, value)
            elif arg == 'F':
                value = frame.operand_stack.pop_float()
                n_frame.local_vars.add_float(i, value)
            elif arg == 'D':
                value = frame.operand_stack.pop_double()
                n_frame.local_vars.add_double(i, value)
            elif arg[0] == 'L':
                jref = frame.operand_stack.pop_ref()
                n_frame.local_vars.add_ref(i, jref)


class IRETURN(Instruction):
    code = 0xac
    name = 'ireturn'

    def execute(self, frame):
        frame.thread.pop_frame()
        r_value = frame.operand_stack.pop_int()
        c_frame = frame.thread.top_frame()
        c_frame.operand_stack.push_int(r_value)


class LRETURN(Instruction):
    code = 0xad
    name = 'lreturn'

    def execute(self, frame):
        frame.thread.pop_frame()
        r_value = frame.operand_stack.pop_long()
        c_frame = frame.thread.top_frame()
        c_frame.operand_stack.push_long(r_value)


class FRETURN(Instruction):
    code = 0xae
    name = 'freturn'

    def execute(self, frame):
        frame.thread.pop_frame()
        r_value = frame.operand_stack.pop_float()
        c_frame = frame.thread.top_frame()
        c_frame.operand_stack.push_float(r_value)


class DRETURN(Instruction):
    code = 0xaf
    name = 'dreturn'

    def execute(self, frame):
        frame.thread.pop_frame()
        r_value = frame.operand_stack.pop_double()
        c_frame = frame.thread.top_frame()
        c_frame.operand_stack.push_double(r_value)


class ARETURN(Instruction):
    code = 0xb0
    name = 'areturn'

    def execute(self, frame):
        frame.thread.pop_frame()
        r_value = frame.operand_stack.pop_ref()
        c_frame = frame.thread.top_frame()
        c_frame.operand_stack.push_ref(r_value)


class ISTORE_N(Instruction):
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

    def get_index(self):
        return 0


class ISTORE_1(ISTORE_N):
    code = 0x3c
    name = 'istore_1'

    def get_index(self):
        return 1


class ISTORE_2(ISTORE_N):
    code = 0x3d
    name = 'istore_2'

    def get_index(self):
        return 2


class ISTORE_3(ISTORE_N):
    code = 0x3e
    name = 'istore_3'

    def get_index(self):
        return 3


class DSTORE_N(Instruction):
    @abc.abstractmethod
    def get_index(self):
        pass

    def execute(self, frame):
        value = frame.operand_stack.pop_double()
        index = self.get_index()
        frame.local_vars.add_double(index, value)


class DSTORE(DSTORE_N):
    code = 0x39
    name = 'dstore'

    def __init__(self):
        super(DSTORE, self).__init__()
        self.index = 0

    def read_operands(self, code_parser):
        self.index = code_parser.read_op()

    def get_index(self):
        return self.index


class DSTORE_0(DSTORE_N):
    code = 0x47
    name = 'dstore_0'

    def get_index(self):
        return 0


class DSTORE_1(DSTORE_N):
    code = 0x48
    name = 'dstore_1'

    def get_index(self):
        return 1


class DSTORE_2(DSTORE_N):
    code = 0x49
    name = 'dstore_2'

    def get_index(self):
        return 2


class DSTORE_3(DSTORE_N):
    code = 0x4a
    name = 'dstore_3'

    def get_index(self):
        return 3


class FSTORE_N(Instruction):
    @abc.abstractmethod
    def get_index(self):
        pass

    def execute(self, frame):
        value = frame.operand_stack.pop_float()
        index = self.get_index()
        frame.local_vars.add_float(index, value)


class FSTORE(FSTORE_N):
    code = 0x38
    name = 'fstore'

    def __init__(self):
        super(FSTORE, self).__init__()
        self.index = 0

    def read_operands(self, code_parser):
        self.index = code_parser.read_op()

    def get_index(self):
        return self.index


class FSTORE_0(FSTORE_N):
    code = 0x43
    name = 'fstore_0'

    def get_index(self):
        return 0


class FSTORE_1(FSTORE_N):
    code = 0x44
    name = 'fstore_1'

    def get_index(self):
        return 1


class FSTORE_2(FSTORE_N):
    code = 0x45
    name = 'fstore_2'

    def get_index(self):
        return 2


class FSTORE_3(FSTORE_N):
    code = 0x46
    name = 'fstore_3'

    def get_index(self):
        return 3


class LSTORE_N(Instruction):
    @abc.abstractmethod
    def get_index(self):
        pass

    def execute(self, frame):
        value = frame.operand_stack.pop_long()
        index = self.get_index()
        frame.local_vars.add_long(index, value)


class LSTORE(LSTORE_N):
    code = 0x37
    name = 'lstore'

    def __init__(self):
        super(LSTORE, self).__init__()
        self.index = 0

    def read_operands(self, code_parser):
        self.index = code_parser.read_op()

    def get_index(self):
        return self.index


class LSTORE_0(LSTORE_N):
    code = 0x3f
    name = 'lstore_0'

    def get_index(self):
        return 0


class LSTORE_1(LSTORE_N):
    code = 0x40
    name = 'lstore_1'

    def get_index(self):
        return 1


class LSTORE_2(LSTORE_N):
    code = 0x41
    name = 'lstore_2'

    def get_index(self):
        return 2


class LSTORE_3(LSTORE_N):
    code = 0x42
    name = 'lstore_3'

    def get_index(self):
        return 3


class LDC(Instruction):
    code = 0x12
    name = 'ldc'

    def __init__(self):
        super(LDC, self).__init__()
        self.index = None

    def read_operands(self, code_parser):
        self.index = code_parser.read_op()

    def execute(self, frame):
        constants = frame.method.jclass.constant_pool.constants
        ref = constants[self.index]
        operand_stack = frame.operand_stack
        if isinstance(ref, JInteger):
            operand_stack.push_int(ref.data)
        elif isinstance(ref, JFloat):
            operand_stack.push_float(ref.data)
        elif isinstance(ref, JString):
            operand_stack.push_ref(ref)
        elif isinstance(ref, JRef):
            operand_stack.push_ref(ref)
        else:
            operand_stack.push(None)


class LDC_W(LDC):
    code = 0x13
    name = 'ldc_w'

    def read_operands(self, code_parser):
        index1 = code_parser.read_op()
        index2 = code_parser.read_op()
        self.index = (index1 << 8) | index2


class LDC2_W(Instruction):
    code = 0x14
    name = 'ldc2_w'

    def __init__(self):
        super(LDC2_W, self).__init__()
        self.index = None

    def read_operands(self, code_parser):
        index1 = code_parser.read_op()
        index2 = code_parser.read_op()
        self.index = (index1 << 8) | index2

    def execute(self, frame):
        constants = frame.method.jclass.constant_pool.constants
        ref = constants[self.index]
        operand_stack = frame.operand_stack
        if isinstance(ref, JLong):
            operand_stack.push_long(ref.data)
        elif isinstance(ref, JDouble):
            operand_stack.push_double(ref.data)
        elif isinstance(ref, JString):
            operand_stack.push_ref(ref)
        else:  # TODO: Class 对象
            pass


class NOP(Instruction):
    code = 0x00
    name = 'nop'

    def execute(self, frame):
        pass


class IF_COND(JUMP_INC):
    def __init__(self):
        super(IF_COND, self).__init__()
        self.branch = 0

    @abc.abstractmethod
    def compare(self, value):
        pass

    def read_operands(self, code_parser):
        branch1 = code_parser.read_op()
        branch2 = code_parser.read_op()
        self.branch = common_utils.get_short_from_bytes(branch1, branch2)

    def execute(self, frame):
        value = frame.operand_stack.pop_int()
        if self.compare(value):
            self.jump_by(frame, self.branch)


class IFEQ(IF_COND):
    code = 0x99
    name = 'ifeq'

    def compare(self, value):
        return value == 0


class IFNE(IF_COND):
    code = 0x9a
    name = 'ifne'

    def compare(self, value):
        return value != 0


class IFLT(IF_COND):
    code = 0x9b
    name = 'iflt'

    def compare(self, value):
        return value < 0


class IFGE(IF_COND):
    code = 0x9c
    name = 'ifge'

    def compare(self, value):
        return value >= 0


class IFGT(IF_COND):
    code = 0x9d
    name = 'ifgt'

    def compare(self, value):
        return value > 0


class IFLE(IF_COND):
    code = 0x9e
    name = 'ifle'

    def compare(self, value):
        return value <= 0


class IF_ICMP_COND(JUMP_INC):
    def __init__(self):
        super(IF_ICMP_COND, self).__init__()
        self.branch = 0

    @abc.abstractmethod
    def compare(self, value1, value2):
        pass

    def read_operands(self, code_parser):
        branch1 = code_parser.read_op()
        branch2 = code_parser.read_op()
        self.branch = common_utils.get_short_from_bytes(branch1, branch2)

    def execute(self, frame):
        value2 = frame.operand_stack.pop_int()
        value1 = frame.operand_stack.pop_int()
        if self.compare(value1, value2):
            self.jump_by(frame, self.branch)


class IF_ICMPEQ(IF_ICMP_COND):
    code = 0x9f
    name = 'if_icmpeq'

    def compare(self, value1, value2):
        return value1 == value2


class IF_ICMPNE(IF_ICMP_COND):
    code = 0xa0
    name = 'if_icmpne'

    def compare(self, value1, value2):
        return value1 != value2


class IF_ICMPLT(IF_ICMP_COND):
    code = 0xa1
    name = 'if_icmplt'

    def compare(self, value1, value2):
        return value1 < value2


class IF_ICMPGE(IF_ICMP_COND):
    code = 0xa2
    name = 'if_icmpge'

    def compare(self, value1, value2):
        return value1 >= value2


class IF_ICMPGT(IF_ICMP_COND):
    code = 0xa3
    name = 'if_icmpgt'

    def compare(self, value1, value2):
        return value1 > value2


class IF_ICMPLE(IF_ICMP_COND):
    code = 0xa4
    name = 'if_icmple'

    def compare(self, value1, value2):
        return value1 <= value2


class IF_ACMP_COND(JUMP_INC):
    def __init__(self):
        super(IF_ACMP_COND, self).__init__()
        self.branch = 0

    @abc.abstractmethod
    def compare(self, ref1, ref2):
        pass

    def read_operands(self, code_parser):
        branch1 = code_parser.read_op()
        branch2 = code_parser.read_op()
        self.branch = common_utils.get_short_from_bytes(branch1, branch2)

    def execute(self, frame):
        # TODO: ref 怎么做比较?
        value2 = frame.operand_stack.pop_ref()
        value1 = frame.operand_stack.pop_ref()
        if self.compare(value1, value2):
            self.jump_by(frame, self.branch)


class IF_ACMPEQ(IF_ACMP_COND):
    code = 0xa5
    name = 'if_acmpeq'

    def compare(self, ref1, ref2):
        return ref1 == ref2


class IF_ACMPNE(IF_ACMP_COND):
    code = 0xa6
    name = 'if_acmpne'

    def compare(self, ref1, ref2):
        return ref1 != ref2


# impdep1 impdep2 breakpoint 为保留操作符
class IMPDEP1(Instruction):
    code = 0xfe
    name = 'impdep1'

    def execute(self, frame):
        pass


class IMPDEP2(Instruction):
    code = 0xff
    name = 'impdep2'

    def execute(self, frame):
        pass


class Breakpoint(Instruction):
    code = 0xca
    name = 'breakpoint'

    def execute(self, frame):
        pass


class NEW(Instruction):
    code = 0xbb
    name = 'new'

    def __init__(self):
        super(NEW, self).__init__()
        self.index = -1

    def read_operands(self, code_parser):
        index1 = code_parser.read_op()
        index2 = code_parser.read_op()
        self.index = (index1 << 8) | index2

    def execute(self, frame):
        class_loader = frame.method.jclass.class_loader
        if class_loader is None:
            class_loader = ClassLoader()
            frame.method.jclass.class_loader = class_loader
        constant_pool = frame.method.jclass.constant_pool
        ref = constant_pool.constants[self.index]
        jclass = class_loader.load_class(ref.class_name)
        ref = JRef.new_object(jclass)  # JObject.new_object() 返回的是真实实例对象  JRef.new_object() 返回的是引用，并且会吧 object 放入 gc 堆
        frame.operand_stack.push_ref(ref)


class NEWARRAY(Instruction):
    code = 0xbc
    name = 'newarray'

    def __init__(self):
        self.atype = None

    def read_operands(self, code_parser):
        self.atype = code_parser.read_op()

    def execute(self, frame):
        count = frame.operand_stack.pop_int()
        class_loader = frame.method.jclass.class_loader
        if class_loader is None:
            class_loader = ClassLoader()
            frame.method.jclass.class_loader = class_loader
        jclass = class_loader.load_class(JArray.get_array_jclass_name(self.atype))
        jref = JRef.new_array(jclass, self.atype, count)
        frame.operand_stack.push_ref(jref)


class ANEWARRAY(Instruction):
    code = 0xbd
    name = 'anewarray'

    def __init__(self):
        super(ANEWARRAY, self).__init__()
        self.index = 0

    def read_operands(self, code_parser):
        index1 = code_parser.read_op()
        index2 = code_parser.read_op()
        self.index = (index1 << 8) | index2

    def execute(self, frame):
        count = frame.operand_stack.pop_int()
        class_loader = frame.method.jclass.class_loader
        if class_loader is None:
            class_loader = ClassLoader()
            frame.method.jclass.class_loader = class_loader
        clref = frame.method.jclass.constant_pool.constants[self.index]
        jclass = class_loader.load_class(JArray.get_ref_array_jclass_name(clref.class_name))
        jref = JRef.new_ref_array(jclass, clref, count)
        frame.operand_stack.push_ref(jref)


class ARRAY_LENGTH(Instruction):
    code = 0xbe
    name = 'arraylength'

    def execute(self, frame):
        ref = frame.operand_stack.pop_ref()
        InsUtils.check_ref_null(ref)
        if ref.handler.obj is None:
            error_handler.rise_null_point_error()
        obj = ref.handler.obj
        if not isinstance(ref.handler.obj, JArray):
            error_handler.rise_runtime_error('!!! not array !!!')
        frame.operand_stack.push_int(obj.length)


class POP(Instruction):
    code = 0x57
    name = 'pop'

    def execute(self, frame):
        frame.operand_stack.pop_raw()


class POP2(Instruction):
    code = 0x58
    name = 'pop2'

    def execute(self, frame):
        frame.operand_stack.pop()
        if frame.operand_stack.is_top_type1():
            frame.operand_stack.pop()


class PUTFIELD(Instruction):
    code = 0xb5
    name = 'putfield'

    def __init__(self):
        super(PUTFIELD, self).__init__()
        self.index = 0

    def read_operands(self, code_parser):
        index1 = code_parser.read_op()
        index2 = code_parser.read_op()
        self.index = (index1 << 8) | index2

    @staticmethod
    def check_state(frame, field_ref, cl_ref):
        if field_ref.is_static():
            error_handler.rise_runtime_error('java.lang.IncompatibleClassChangeError: put field to static value')
        if field_ref.is_final() and frame.method.name != '<init>':
            error_handler.rise_runtime_error('java.lang.IllegalAccessError: val is final')
        if cl_ref is None or cl_ref.handler is None or cl_ref.handler.obj is None:
            error_handler.rise_runtime_error('java.lang.NullPointerException ref is null')

    def execute(self, frame):
        # TODO: field 验证
        field_ref = frame.method.jclass.constant_pool.constants[self.index]
        val = frame.operand_stack.pop()
        cl_ref = frame.operand_stack.pop_ref()
        PUTFIELD.check_state(frame, field_ref, cl_ref)
        if isinstance(val, JRef):
            InsUtils.check_ref_null(cl_ref)
            cl_ref.handler.obj.put_ref_field(field_ref.name, val)
        else:
            cl_ref.handler.obj.put_field(field_ref.name, val)


class GETFIELD(Instruction):
    code = 0xb4
    name = 'getfield'

    def __init__(self):
        super(GETFIELD, self).__init__()
        self.index = 0

    def read_operands(self, code_parser):
        index1 = code_parser.read_op()
        index2 = code_parser.read_op()
        self.index = (index1 << 8) | index2

    def execute(self, frame):
        fieldref = frame.method.jclass.constant_pool.constants[self.index]
        clref = frame.operand_stack.pop_ref()
        InsUtils.check_ref_null(clref)
        InsUtils.check_ref_null(clref)
        val = clref.handler.obj.get_field(fieldref.name)
        ftype = InsUtils.get_type_by_descriptor(fieldref.descriptor)
        if ftype == InsUtils.TYPE_INT:
            frame.operand_stack.push_int(val)
        elif ftype == InsUtils.TYPE_FLOAT:
            frame.operand_stack.push_float(val)
        elif ftype == InsUtils.TYPE_LONG:
            frame.operand_stack.push_long(val)
        elif ftype == InsUtils.TYPE_DOUBLE:
            frame.operand_stack.push_double(val)
        elif ftype == InsUtils.TYPE_REF or ftype == InsUtils.TYPE_ARRAY:
            frame.operand_stack.push_ref(val)


class RETURN(Instruction):
    code = 0xb1
    name = 'return'

    def __init__(self):
        super(RETURN, self).__init__()

    def execute(self, frame):
        frame.thread.pop_frame()


class SIPUSH(Instruction):
    code = 0x11
    name = 'sipush'

    def __init__(self):
        super(SIPUSH, self).__init__()
        self.byte = 0

    def read_operands(self, code_parser):
        byte1 = code_parser.read_op()
        byte2 = code_parser.read_op()
        self.byte = (byte1 << 8) | byte2

    def execute(self, frame):
        frame.operand_stack.push_int(ctypes.c_short(self.byte).value)


class SWAP(Instruction):
    code = 0x5f
    name = 'swap'

    def execute(self, frame):
        value1 = frame.operand_stack.pop()


class TABLE_SWITCH(JUMP_INC):
    code = 0xaa
    name = 'tableswitch'

    def __init__(self):
        super(TABLE_SWITCH, self).__init__()
        self.default = 0
        self.low = 0
        self.high = 0
        self.count = 0
        self.offsets = []

    def read_operands(self, code_parser):
        code_parser.skip_padding()

        self.default = code_parser.read_4byte()

        self.low = code_parser.read_4byte()

        self.high = code_parser.read_4byte()

        self.count = self.high - self.low + 1

        for i in range(self.count):
            offset = code_parser.read_4byte()
            self.offsets.append(offset)

    def execute(self, frame):
        index = frame.operand_stack.pop_int()
        if index < self.low or index > self.high:
            self.jump_by(frame, self.default)
        else:
            self.jump_by(frame, self.offsets[index - self.low])


class LOOK_UP_SWITCH(JUMP_INC):
    code = 0xab
    name = 'lookupswitch'

    def __init__(self):
        super(LOOK_UP_SWITCH, self).__init__()
        self.default = 0
        self.npairs = 0
        self.pairs = {}

    def read_operands(self, code_parser):
        code_parser.skip_padding()

        self.default = code_parser.read_4byte()
        self.npairs = code_parser.read_4byte()

        for i in range(self.npairs):
            match = code_parser.read_4byte()
            offset = code_parser.read_4byte()
            self.pairs[match] = offset

    def execute(self, frame):
        pairs = self.pairs
        key = frame.operand_stack.pop_int()
        if key in pairs:
            self.jump_by(frame, pairs[key])
        else:
            self.jump_by(frame, self.default)


class CHECK_CAST(Instruction):
    code = 0xc0
    name = 'checkcast'

    def __init__(self):
        super(CHECK_CAST, self).__init__()
        self.index = 0

    def read_operands(self, code_parser):
        index1 = code_parser.read_op()
        index2 = code_parser.read_op()
        self.index = (index1 << 8) | index2

    def execute(self, frame):
        # TODO: interface 实现
        ref = frame.operand_stack.top()
        if not isinstance(ref, JRef):
            error_handler.rise_runtime_error('checkcast param must be ref')
        cl_ref = frame.method.jclass.constant_pool.constants[self.index]
        name = cl_ref.class_name
        cast_class = ref.handler.obj.jclass
        while cast_class is not None:
            if cast_class.name == name:
                return
            cast_class = cast_class.super_class
        error_handler.rise_class_cast_error()


class INSTANCE_OF(Instruction):
    code = 0xc1
    name = 'instanceof'

    def __init__(self):
        super(INSTANCE_OF, self).__init__()
        self.index = 0

    def read_operands(self, code_parser):
        index1 = code_parser.read_op()
        index2 = code_parser.read_op()
        self.index = (index1 << 8) | index2

    def execute(self, frame):
        # TODO: interface 实现
        ref = frame.operand_stack.top()
        if not isinstance(ref, JRef):
            error_handler.rise_runtime_error('instance param must be ref')
        cl_ref = frame.method.jclass.constant_pool.constants[self.index]
        name = cl_ref.class_name
        if ref.handler is None:
            frame.operand_stack.push_int(0)
            return
        cast_class = ref.handler.obj.jclass
        while cast_class is not None:
            if cast_class.name == name:
                frame.operand_stack.push_int(1)
                return
            cast_class = cast_class.super_class
        frame.operand_stack.push_int(0)


class WIDE(Instruction):
    code = 0xc4
    name = 'wide'

    def __init__(self):
        super(WIDE, self).__init__()
        self.code = None
        self.index = 0
        self.const = 0
        self.ins = None
        self.type1_code_map = {
            ILOAD.code: ILOAD,
            FLOAD.code: FLOAD,
            ALOAD.code: ALOAD,
            LLOAD.code: LLOAD,
            DLOAD.code: DLOAD,
            ISTORE.code: ISTORE,
            FSTORE.code: FSTORE,
            ASTORE.code: ASTORE,
            LSTORE.code: LSTORE,
            DSTORE.code: DSTORE,
        }
        self.type2_code_map = {
            IINC.code: IINC
        }

    def read_operands(self, code_parser):
        self.code = code_parser.read_op()
        index1 = code_parser.read_op()
        index2 = code_parser.read_op()
        self.index = (index1 << 8) | index2
        if self.code in self.type1_code_map:
            ins = self.type1_code_map[self.code]()
            ins.index = self.index
            self.ins = ins
        elif self.code in self.type2_code_map:
            ins = self.type2_code_map[self.code]()
            ins.index = self.index
            const1 = code_parser.read_op()
            const2 = code_parser.read_op()
            self.const = (const1 << 8) | const2
            ins.const = self.const
            self.ins = ins

    def execute(self, frame):
        self.ins.execute(frame)


class IF_NULL(JUMP_INC):
    code = 0xc6
    name = 'ifnull'

    def __init__(self):
        super(IF_NULL, self).__init__()
        self.branch = 0

    def read_operands(self, code_parser):
        branch1 = code_parser.read_op()
        branch2 = code_parser.read_op()
        self.branch = (branch1 << 8) | branch2

    def execute(self, frame):
        ref = frame.operand_stack.pop_ref()
        if ref is None or ref.handler is None or ref.handler.obj is None:
            self.jump_by(frame, self.branch)


class IF_NON_NULL(JUMP_INC):
    code = 0xc7
    name = 'ifnonnull'

    def __init__(self):
        super(IF_NON_NULL, self).__init__()
        self.branch = 0

    def read_operands(self, code_parser):
        branch1 = code_parser.read_op()
        branch2 = code_parser.read_op()
        self.branch = (branch1 << 8) | branch2

    def execute(self, frame):
        ref = frame.operand_stack.pop_ref()
        if ref is not None and ref.handler is not None and ref.handler.obj is not None:
            self.jump_by(frame, self.branch)


class ATHROW(JUMP_INC):
    code = 0xbf
    name = 'athrow'

    def execute(self, frame):
        thread = frame.thread
        ref = frame.operand_stack.pop_ref()
        exceptions = frame.method.exceptions
        InsUtils.check_ref_null(ref)
        catched = False
        while exceptions is not None:
            for ex in exceptions:
                cl_ref = frame.method.jclass.constant_pool.constants[ex.catch_type]
                jclass = ref.handler.obj.jclass
                while jclass is not None and jclass.name != 'java/lang/Object':
                    if cl_ref.class_name == jclass.name:
                        frame.operand_stack.clear()
                        frame.operand_stack.push_ref(ref)
                        self.jump_to(frame, ex.handler_pc)
                        catched = True
                        break
                    jclass = jclass.super_class
                if catched:
                    break
            if catched:
                break
            thread.pop_frame()
            if not thread.has_frame():
                break
            frame = thread.top_frame()
            exceptions = frame.method.exceptions
        if not catched:
            error_handler.rise_runtime_error('none catched exception: ' + ref.handler.obj.jclass.name)


instruction_cache = dict()


def register_instruction(ins):
    instruction_cache[ins.code] = ins


register_instruction(NOP)
register_instruction(ACONST_NULL)
register_instruction(ALOAD)
register_instruction(ALOAD_0)
register_instruction(ALOAD_1)
register_instruction(ALOAD_2)
register_instruction(ALOAD_3)
register_instruction(ASTORE)
register_instruction(ASTORE_0)
register_instruction(ASTORE_1)
register_instruction(ASTORE_2)
register_instruction(ASTORE_3)
register_instruction(ARETURN)
register_instruction(BIPUSH)
register_instruction(DUP)
register_instruction(DUP_X1)
register_instruction(DUP_X2)
register_instruction(DUP2)
register_instruction(DUP2_X1)
register_instruction(DUP2_X2)
register_instruction(GETSTATIC)
register_instruction(PUTSTATIC)
register_instruction(GOTO)
register_instruction(GOTO_W)
register_instruction(IADD)
register_instruction(LADD)
register_instruction(FADD)
register_instruction(DADD)
register_instruction(ISUB)
register_instruction(FSUB)
register_instruction(LSUB)
register_instruction(DSUB)
register_instruction(IMUL)
register_instruction(LMUL)
register_instruction(FMUL)
register_instruction(DMUL)
register_instruction(IDIV)
register_instruction(LDIV)
register_instruction(FDIV)
register_instruction(DDIV)
register_instruction(IREM)
register_instruction(LREM)
register_instruction(FREM)
register_instruction(DREM)
register_instruction(INEG)
register_instruction(LNEG)
register_instruction(FNEG)
register_instruction(DNEG)
register_instruction(ISHL)
register_instruction(LSHL)
register_instruction(ISHR)
register_instruction(LSHR)
register_instruction(IUSHR)
register_instruction(LUSHR)
register_instruction(IAND)
register_instruction(LAND)
register_instruction(IOR)
register_instruction(LOR)
register_instruction(IXOR)
register_instruction(LXOR)
register_instruction(IINC)
register_instruction(I2L)
register_instruction(I2F)
register_instruction(I2D)
register_instruction(L2I)
register_instruction(L2F)
register_instruction(L2D)
register_instruction(F2I)
register_instruction(F2L)
register_instruction(F2D)
register_instruction(D2I)
register_instruction(D2L)
register_instruction(D2F)
register_instruction(I2B)
register_instruction(I2C)
register_instruction(I2S)
register_instruction(LCMP)
register_instruction(FCMPL)
register_instruction(FCMPD)
register_instruction(DCMPL)
register_instruction(DCMPD)
register_instruction(IFEQ)
register_instruction(IFNE)
register_instruction(IFLT)
register_instruction(IFGE)
register_instruction(IFGT)
register_instruction(IFLE)
register_instruction(ICONST_M1)
register_instruction(ICONST_0)
register_instruction(ICONST_1)
register_instruction(ICONST_2)
register_instruction(ICONST_3)
register_instruction(ICONST_4)
register_instruction(ICONST_5)
register_instruction(LCONST_0)
register_instruction(LCONST_1)
register_instruction(FCONST_0)
register_instruction(FCONST_1)
register_instruction(FCONST_2)
register_instruction(DCONST_0)
register_instruction(DCONST_1)
register_instruction(IF_ICMPEQ)
register_instruction(IF_ICMPGE)
register_instruction(IF_ICMPGT)
register_instruction(IF_ICMPLE)
register_instruction(IF_ICMPLT)
register_instruction(IF_ICMPNE)
register_instruction(IF_ACMPEQ)
register_instruction(IF_ACMPNE)
register_instruction(DLOAD)
register_instruction(DLOAD_0)
register_instruction(DLOAD_1)
register_instruction(DLOAD_2)
register_instruction(DLOAD_3)
register_instruction(FLOAD)
register_instruction(FLOAD_0)
register_instruction(FLOAD_1)
register_instruction(FLOAD_2)
register_instruction(FLOAD_3)
register_instruction(ILOAD)
register_instruction(ILOAD_0)
register_instruction(ILOAD_1)
register_instruction(ILOAD_2)
register_instruction(ILOAD_3)
register_instruction(LLOAD)
register_instruction(LLOAD_0)
register_instruction(LLOAD_1)
register_instruction(LLOAD_2)
register_instruction(LLOAD_3)
register_instruction(DSTORE)
register_instruction(DSTORE_0)
register_instruction(DSTORE_1)
register_instruction(DSTORE_2)
register_instruction(DSTORE_3)
register_instruction(FSTORE)
register_instruction(FSTORE_0)
register_instruction(FSTORE_1)
register_instruction(FSTORE_2)
register_instruction(FSTORE_3)
register_instruction(IASTORE)
register_instruction(IALOAD)
register_instruction(CASTORE)
register_instruction(CALOAD)
register_instruction(DASTORE)
register_instruction(DALOAD)
register_instruction(FASTORE)
register_instruction(FALOAD)
register_instruction(LASTORE)
register_instruction(LALOAD)
register_instruction(SASTORE)
register_instruction(SALOAD)
register_instruction(AASTORE)
register_instruction(AALOAD)
register_instruction(BASTORE)
register_instruction(BALOAD)
register_instruction(ISTORE)
register_instruction(ISTORE_0)
register_instruction(ISTORE_1)
register_instruction(ISTORE_2)
register_instruction(ISTORE_3)
register_instruction(LSTORE)
register_instruction(LSTORE_0)
register_instruction(LSTORE_1)
register_instruction(LSTORE_2)
register_instruction(LSTORE_3)
register_instruction(IMPDEP1)
register_instruction(IMPDEP2)
register_instruction(INVOKESPECIAL)
register_instruction(INVOKESTATIC)
register_instruction(INVOKEVIRTUAL)
register_instruction(RETURN)
register_instruction(IRETURN)
register_instruction(LRETURN)
register_instruction(FRETURN)
register_instruction(DRETURN)
register_instruction(ARETURN)
register_instruction(LDC)
register_instruction(LDC_W)
register_instruction(LDC2_W)
register_instruction(NEW)
register_instruction(NEWARRAY)
register_instruction(ANEWARRAY)
register_instruction(ARRAY_LENGTH)
register_instruction(POP)
register_instruction(POP2)
register_instruction(PUTFIELD)
register_instruction(GETFIELD)
register_instruction(SIPUSH)
register_instruction(SWAP)
register_instruction(TABLE_SWITCH)
register_instruction(LOOK_UP_SWITCH)
register_instruction(CHECK_CAST)
register_instruction(INSTANCE_OF)
register_instruction(WIDE)
register_instruction(IF_NULL)
register_instruction(IF_NON_NULL)
register_instruction(ATHROW)


def get_instruction(code):
    if code in instruction_cache:
        return instruction_cache[code]()
    error_handler.rise_runtime_error('sorry! code %x is not realized!' % code)


if __name__ == '__main__':
    print(sorted(instruction_cache))
    for code in range(255):
        if code not in instruction_cache:
            print('%x' % code)
