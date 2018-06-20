# coding=utf-8

import abc
import struct

from runtime.thread import Frame, LocalVars
from runtime.jclass import ClassLoader, JString, JDouble, JLong, JClass, JFloat, JInteger
from runtime.jobject import JObject, JArray, JRef
from base.utils import print_utils, common_utils, error_handler
from interpreter.code_parser import CodeParser
from jthread.jthread import JThread


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
            if m.name == '<cinit>':
                method = m
                break
        if method is not None:
            n_frame = Frame(frame.thread, method)
            frame.thread.add_frame(n_frame)
            frame.pc = frame.thread.pc


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
        frame.operand_stack.push_int(self.byte)


class DUP(Instruction):
    code = 0x59
    name = 'dup'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        value = operand_stack.top()
        if isinstance(value, JRef):
            value = value.clone()
        operand_stack.push(value)


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
        jclass = ref.cache_class
        if not jclass.has_inited:
            frame.pc = frame.thread.pc
            c_init = INNER_INVOKE_C_INIT(jclass)
            c_init.execute(frame)
            jclass.has_inited = True
            return
        slots = jclass.static_fields
        val = slots[ref.field.name]
        if val is not None:
            if val.num is not None:
                frame.operand_stack.push(val.num)
            elif val.ref is not None:
                frame.operand_stack.push(val.ref)
            else:  # TODO: 兼容 System.out.println()
                frame.operand_stack.push(None)
        else:  # TODO: 兼容 System.out.println()
            frame.operand_stack.push(None)


class JUMP_INC(Instruction):
    def jump_by(self, frame, offset):
        frame.pc = frame.thread.pc + offset


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


class IASTORE(Instruction):
    code = 0x4f
    name = 'iastore'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        value = operand_stack.pop_int()
        index = operand_stack.pop_int()
        aref = operand_stack.pop_ref()
        aref.handler.obj.add_item(index, value)


class IALOAD(Instruction):
    code = 0x2e
    name = 'iaload'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        index = operand_stack.pop_int()
        aref = operand_stack.pop_ref()
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
        aref.handler.obj.add_item(index, value)


class CALOAD(Instruction):
    code = 0x34
    name = 'caload'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        index = operand_stack.pop_int()
        aref = operand_stack.pop_ref()
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
        aref.handler.obj.add_item(index, value)


class DALOAD(Instruction):
    code = 0x31
    name = 'daload'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        index = operand_stack.pop_int()
        aref = operand_stack.pop_ref()
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
        aref.handler.obj.add_item(index, value)


class FALOAD(Instruction):
    code = 0x30
    name = 'faload'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        index = operand_stack.pop_int()
        aref = operand_stack.pop_ref()
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
        aref.handler.obj.add_item(index, value)


class LALOAD(Instruction):
    code = 0x2f
    name = 'laload'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        index = operand_stack.pop_int()
        aref = operand_stack.pop_ref()
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
        aref.handler.obj.add_item(index, value)


class SALOAD(Instruction):
    code = 0x35
    name = 'saload'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        index = operand_stack.pop_int()
        aref = operand_stack.pop_ref()
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
        aref.handler.obj.add_ref_item(index, value)


class AALOAD(Instruction):
    code = 0x32
    name = 'aaload'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        index = operand_stack.pop_int()
        aref = operand_stack.pop_ref()
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
        aref.handler.obj.add_item(index, value)


class BALOAD(Instruction):
    code = 0x33
    name = 'baload'

    def execute(self, frame):
        operand_stack = frame.operand_stack
        index = operand_stack.pop_int()
        aref = operand_stack.pop_ref()
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
        n_method = n_method_ref.resolve_method_with_super(frame.method.jclass.class_loader)
        n_frame = Frame(frame.thread, n_method)
        frame.thread.add_frame(n_frame)
        arg_desc = n_method.arg_desc
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
        else:  # TODO: Class 对象
            pass


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


class POP(Instruction):
    code = 0x57
    name = 'pop'

    def execute(self, frame):
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

    def execute(self, frame):
        fieldref = frame.method.jclass.constant_pool.constants[self.index]
        val = frame.operand_stack.pop()
        clref = frame.operand_stack.pop_ref()
        if isinstance(val, JRef):
            clref.handler.obj.put_ref_field(fieldref.name, val)
        else:
            clref.handler.obj.put_field(fieldref.name, val)


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
        val = clref.handler.obj.get_field(fieldref.name)
        frame.operand_stack.push(val)


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
        frame.operand_stack.push_int(self.byte)


instruction_cache = dict()


def register_instruction(ins):
    instruction_cache[ins.code] = ins


register_instruction(NOP)
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
register_instruction(GETSTATIC)
register_instruction(GOTO)
register_instruction(IADD)
register_instruction(IINC)
register_instruction(ICONST_M1)
register_instruction(ICONST_0)
register_instruction(ICONST_1)
register_instruction(ICONST_2)
register_instruction(ICONST_3)
register_instruction(ICONST_4)
register_instruction(ICONST_5)
register_instruction(LCONST_0)
register_instruction(LCONST_1)
register_instruction(IF_ICMPEQ)
register_instruction(IF_ICMPGE)
register_instruction(IF_ICMPGT)
register_instruction(IF_ICMPLE)
register_instruction(IF_ICMPLT)
register_instruction(IF_ICMPNE)
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
register_instruction(LSTORE_0)
register_instruction(LSTORE_1)
register_instruction(LSTORE_2)
register_instruction(LSTORE_3)
register_instruction(IMPDEP1)
register_instruction(IMPDEP2)
register_instruction(INVOKESPECIAL)
register_instruction(INVOKESTATIC)
register_instruction(INVOKEVIRTUAL)
register_instruction(IRETURN)
register_instruction(LDC)
register_instruction(LDC2_W)
register_instruction(NEW)
register_instruction(NEWARRAY)
register_instruction(ANEWARRAY)
register_instruction(POP)
register_instruction(PUTFIELD)
register_instruction(GETFIELD)
register_instruction(RETURN)
register_instruction(SIPUSH)


def get_instruction(code):
    if code in instruction_cache:
        return instruction_cache[code]()
    error_handler.rise_runtime_error('sorry! code %x is not realized!' % code)
