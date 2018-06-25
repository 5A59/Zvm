# coding=utf-8

from base.utils import common_utils, print_utils
from java_class.class_file import *
from java_class.class_parser import ClassParser
from runtime.thread import Slot
from runtime.heap import Heap
from base.jvm_config import jdk_path

import os


# 对应 java 中的 Class
class JClass(object):
    ACC_PUBLIC = 0x0001
    ACC_PRIVATE = 0x0002
    ACC_PROTECTED = 0x0004
    ACC_STATIC = 0x0008
    ACC_FINAL = 0x0010
    ACC_VOLATILE = 0x0040
    ACC_TRANSIENT = 0x0080
    ACC_SYNTHETIC = 0x1000
    ACC_ENUM = 0x4000

    @staticmethod
    def is_public(flag):
        return flag & JClass.ACC_PUBLIC != 0

    @staticmethod
    def is_private(flag):
        return flag & JClass.ACC_PRIVATE != 0

    @staticmethod
    def is_static(flag):
        return flag & JClass.ACC_STATIC != 0

    def __init__(self):
        self.access_flag = None
        self.name = None
        self.super_class_name = None
        self.super_class = None
        self.interfaces = None
        self.fields = None
        self.methods = None
        self.constant_pool = None
        self.class_loader = None
        self.static_fields = None  # map{ name: Slot }
        self.has_inited = False

    def new_jclass(self, class_file):
        Heap.new_jclass(self)
        self.access_flag = common_utils.get_int_from_bytes(class_file.access_flag)
        self.constant_pool = ConstantPool.new_constant_pool(class_file)
        self.fields = Field.new_fields(class_file.fields, self.constant_pool.constants)
        self.methods = Method.new_methods(self, class_file.methods, self.constant_pool.constants)
        super_class = self.constant_pool.constants[common_utils.get_int_from_bytes(class_file.super_class)]
        if super_class is not None:
            self.super_class_name = super_class.class_name  # 从方法区取
        self.interfaces = None
        self.static_fields = {}
        for sf in self.__get_static_fields():
            desc = sf.descriptor
            slot = Slot()
            if desc == 'B' or desc == 'I' or desc == 'J' or desc == 'S' or desc == 'Z':
                slot.num = 0
            elif desc == 'C':
                slot.num = '0'
            elif desc == 'F':
                slot.num = 0.0
            elif desc == 'D':
                slot.num = 0.0
            self.static_fields[sf.name] = slot

    def get_instance_fields(self):
        return [field for field in self.fields if not JClass.is_static(field.access_flag)]

    # return Field[]
    def __get_static_fields(self):
        return [field for field in self.fields if JClass.is_static(field.access_flag)]

    def get_main_method(self):
        methods = self.methods
        for method in methods:
            if method.name == 'main' and method.descriptor == '([Ljava/lang/String;)V':
                return method
        return None


class ConstantPool(object):
    def __init__(self):
        self.constants = None

    @staticmethod
    def new_constant_pool(class_file):
        r_cp = class_file.constant_pool
        constants = []
        for cp in r_cp:
            if isinstance(cp, ClassInfo):
                constants.append(ClassRef.new_class_ref(r_cp, cp))
            elif isinstance(cp, FieldRefInfo):
                constants.append(FieldRef.new_field_ref(r_cp, cp))
            elif isinstance(cp, MethodRefInfo):
                constants.append(MethodRef.new_method_ref(r_cp, cp))
            elif isinstance(cp, InterfaceMethodRefInfo):
                constants.append(None)
            elif isinstance(cp, StringInfo):
                st = r_cp[common_utils.get_int_from_bytes(cp.string_index)]
                st = common_utils.get_string_from_bytes(st.bytes)
                jstring = JString()
                jstring.data = st
                constants.append(jstring)
            elif isinstance(cp, IntegerInfo):
                jint = JInteger()
                jint.data = common_utils.get_int_from_bytes(cp.bytes)
                constants.append(jint)
            elif isinstance(cp, FloatInfo):
                jfloat = JFloat()
                jfloat.data = common_utils.get_float_from_bytes(cp.bytes)
                constants.append(jfloat)
            elif isinstance(cp, LongInfo):
                jlong = JLong()
                jlong.data = common_utils.get_long_from_bytes(cp.high_bytes, cp.low_bytes)
                constants.append(jlong)
            elif isinstance(cp, DoubleInfo):
                jdouble = JDouble()
                jdouble.data = common_utils.get_double_from_bytes(cp.high_bytes, cp.low_bytes)
                constants.append(jdouble)
            elif isinstance(cp, NameAndTypeInfo):
                constants.append(None)
            elif isinstance(cp, Utf8Info):
                constants.append(common_utils.get_string_from_bytes(cp.bytes))
            elif isinstance(cp, MethodHandleInfo):
                constants.append(None)
            else:
                constants.append(None)
        constants_pool = ConstantPool()
        constants_pool.constants = constants
        return constants_pool


def get_attribute(attributes, constant_pool, name):
    for attr in attributes:
        index = common_utils.get_int_from_bytes(attr.attribute_name_index)
        aname = constant_pool[index]
        if aname == name:
            return attr

    return None


class Field(object):
    def __init__(self):
        self.access_flag = None
        self.name = None
        self.descriptor = None
        self.descriptor_index = None
        self.constant_value_index = None
        self.signature = None  # 记录范型变量
        self.type = None  # JClass

    def is_public(self):
        return MemberRef.check_state(self.access_flag, FieldRef.ACC_PUBLIC)

    def is_protected(self):
        return MemberRef.check_state(self.access_flag, FieldRef.ACC_PROTECTED)

    def is_private(self):
        return MemberRef.check_state(self.access_flag, FieldRef.ACC_PRIVATE)

    def is_static(self):
        return MemberRef.check_state(self.access_flag, FieldRef.ACC_STATIC)

    def is_final(self):
        return MemberRef.check_state(self.access_flag, FieldRef.ACC_FINAL)

    def is_volatile(self):
        return MemberRef.check_state(self.access_flag, FieldRef.ACC_VOLATILE)

    def is_transient(self):
        return MemberRef.check_state(self.access_flag, FieldRef.ACC_TRANSIENT)

    @staticmethod
    def new_fields(cf_fields, constant_pool):
        fields = []
        for f in cf_fields:
            nf = Field()
            nf.access_flag = common_utils.get_int_from_bytes(f.access_flags)
            nf.name = constant_pool[common_utils.get_int_from_bytes(f.name_index)]
            nf.descriptor_index = common_utils.get_int_from_bytes(f.descriptor_index)
            nf.descriptor = constant_pool[nf.descriptor_index]
            attr = get_attribute(f.attributes, constant_pool, 'ConstantValue')
            if attr is not None:
                nf.constant_value_index = common_utils.get_int_from_bytes(attr.constant_value_index)
            fields.append(nf)
        return fields


class Method(object):
    def __init__(self):
        self.access_flag = None
        self.name = None
        self.descriptor = None
        self.max_stack = None
        self.max_locals = None
        self.code = None
        self.exceptions = None  # ExceptionTable[]
        self.arg_desc = None
        self.jclass = None

    @staticmethod
    def new_methods(jclass, cf_methods, constant_pool):
        methods = []
        for m in cf_methods:
            nm = Method()
            nm.jclass = jclass
            nm.access_flag = common_utils.get_int_from_bytes(m.access_flags)
            nm.name = constant_pool[common_utils.get_int_from_bytes(m.name_index)]
            nm.descriptor = constant_pool[common_utils.get_int_from_bytes(m.descriptor_index)]
            attr = get_attribute(m.attributes, constant_pool, 'Code')
            nm.max_stack = common_utils.get_int_from_bytes(attr.max_stack)
            nm.max_locals = common_utils.get_int_from_bytes(attr.max_locals)
            nm.code = attr.code
            nm.exceptions = []
            for ex in attr.exception_table:
                jex = JException()
                jex.start_pc = common_utils.get_int_from_bytes(ex.start_pc)
                jex.end_pc = common_utils.get_int_from_bytes(ex.end_pc)
                jex.handler_pc = common_utils.get_int_from_bytes(ex.handler_pc)
                jex.catch_type = common_utils.get_int_from_bytes(ex.catch_type)
                nm.exceptions.append(jex)
            nm.arg_desc = Method.get_arg_desc(nm.descriptor)
            methods.append(nm)
        return methods

    @staticmethod
    def get_arg_desc(descs):
        arg_desc = []
        desc = ''
        for s in descs:
            if s == ')':
                break
            if len(desc) == 0:
                if s == 'B' or s == 'C' or s == 'D' or s == 'F' or s == 'I' or s == 'J' or s == 'S' or s == 'Z':
                    desc = s
                    arg_desc.append(desc)
                    desc = ''
                elif s == 'L':
                    desc += s
            else:
                if desc[0] == 'L':
                    desc += s
                    if s == ';':
                        arg_desc.append(desc)
                        desc = ''
                elif desc[0] == '[':
                    if 'L' in desc:
                        desc += s
                        if s == ';':
                            arg_desc.append(desc)
                            desc = ''
                    else:
                        desc += s
                        if s != '[':
                            arg_desc.append(desc)
                            desc = ''
        return arg_desc


class JException(object):
    def __init__(self):
        self.start_pc = 0
        self.end_pc = 0
        self.handler_pc = 0
        self.catch_type = 0


class Ref(object):
    def __init__(self):
        self.cp = None
        self.class_name = None
        self.cache_class = None  # JClass

    def resolve_class(self, class_loader, need_re_resolve=False, class_name=None):
        if self.cache_class is not None and not need_re_resolve:
            return self.cache_class
        if class_loader is None:
            class_loader = ClassLoader.default_class_loader()
        if class_name is None:
            class_name = self.class_name
        self.cache_class = class_loader.load_class(class_name)
        self.cache_class.class_loader = class_loader
        return self.cache_class


class ClassRef(Ref):
    def __init__(self):
        super(ClassRef, self).__init__()

    @staticmethod
    def new_class_ref(cp, class_info):  # ConstantPool ConstantClassInfo
        cr = ClassRef()
        cr.cp = cp
        tmp = cp[common_utils.get_int_from_bytes(class_info.name_index)]
        cr.class_name = common_utils.get_string_from_bytes(tmp.bytes)
        return cr


class MemberRef(Ref):
    def __init__(self):
        super(MemberRef, self).__init__()
        self.name = None
        self.descriptor = None
        self.access_flag = None

    @staticmethod
    def check_state(flag, state):
        if flag is None:
            return False
        return (flag & state) != 0

    @staticmethod
    def get_string(cp, index_byte):
        return common_utils.get_string_from_bytes(cp[common_utils.get_int_from_bytes(index_byte)].bytes)

    @staticmethod
    def get_obj(cp, index_byte):
        return cp[common_utils.get_int_from_bytes(index_byte)]


class FieldRef(MemberRef):
    ACC_PUBLIC = 0x0001
    ACC_PRIVATE = 0x0002
    ACC_PROTECTED = 0x0004
    ACC_STATIC = 0x0008
    ACC_FINAL = 0x0010
    ACC_VOLATILE = 0x0040
    ACC_TRANSIENT = 0x0080
    ACC_SYNTHETIC = 0x1000
    ACC_ENUM = 0x4000

    def __init__(self):
        super(FieldRef, self).__init__()
        self.field = None

    def is_public(self):
        return MemberRef.check_state(self.access_flag, FieldRef.ACC_PUBLIC)

    def is_protected(self):
        return MemberRef.check_state(self.access_flag, FieldRef.ACC_PROTECTED)

    def is_private(self):
        return MemberRef.check_state(self.access_flag, FieldRef.ACC_PRIVATE)

    def is_static(self):
        return MemberRef.check_state(self.access_flag, FieldRef.ACC_STATIC)

    def is_final(self):
        return MemberRef.check_state(self.access_flag, FieldRef.ACC_FINAL)

    def is_volatile(self):
        return MemberRef.check_state(self.access_flag, FieldRef.ACC_VOLATILE)

    def is_transient(self):
        return MemberRef.check_state(self.access_flag, FieldRef.ACC_TRANSIENT)

    @staticmethod
    def new_field_ref(cp, field_ref_info):
        fr = FieldRef()
        cl = cp[common_utils.get_int_from_bytes(field_ref_info.class_index)]
        fr.class_name = MemberRef.get_string(cp, cl.name_index)
        fr.cp = cp
        name_and_type = MemberRef.get_obj(cp, field_ref_info.name_and_type_index)
        fr.name = MemberRef.get_string(cp, name_and_type.name_index)
        fr.descriptor = MemberRef.get_string(cp, name_and_type.descriptor_index)
        return fr

    def resolve_field(self, class_loader):
        if self.field is not None:
            return self.field
        if self.cache_class is None:
            self.resolve_class(class_loader)
        fields = self.cache_class.fields
        for f in fields:
            if f.name == self.name:
                self.field = f
                break
        return self.field


class MethodRef(MemberRef):
    def __init__(self):
        super(MethodRef, self).__init__()
        self.method = None

    @staticmethod
    def new_method_ref(cp, method_ref_info):
        mr = MethodRef()
        cl = cp[common_utils.get_int_from_bytes(method_ref_info.class_index)]
        mr.class_name = MemberRef.get_string(cp, cl.name_index)
        mr.cp = cp
        name_and_type = MemberRef.get_obj(cp, method_ref_info.name_and_type_index)
        mr.name = MemberRef.get_string(cp, name_and_type.name_index)
        mr.descriptor = MemberRef.get_string(cp, name_and_type.descriptor_index)
        return mr

    # TODO: 方法权限等的处理
    def resolve_method(self, class_loader, need_re_resolve=False, class_name=None):
        if self.method is not None and not need_re_resolve:
            return self.method
        if self.cache_class is None or need_re_resolve:
            self.resolve_class(class_loader, need_re_resolve, class_name)
        methods = self.cache_class.methods
        for m in methods:
            if m.name == self.name and m.descriptor == self.descriptor:
                self.method = m
                break
        return self.method

    def resolve_method_with_super(self, class_loader):
        self.resolve_method(class_loader, True)
        if self.method is None:
            super_class = self.cache_class.super_class
            while super_class is not None:
                for m in super_class.methods:
                    if m.name == self.name:
                        self.method = m
                        break
                if self.method is not None:
                    break
                super_class = super_class.super_class
        return self.method

    def re_resolve_method_with_super_by_class_name(self, class_loader, class_name):
        self.resolve_method(class_loader, True, class_name)
        if self.method is None:
            super_class = self.cache_class.super_class
            while super_class is not None:
                for m in super_class.methods:
                    if m.name == self.name:
                        self.method = m
                        break
                if self.method is not None:
                    break
                super_class = super_class.super_class
        return self.method


class BaseType(object):
    def __init__(self):
        self.data = None


class JInteger(BaseType):
    def __init__(self):
        super(JInteger, self).__init__()


class JFloat(BaseType):
    def __init__(self):
        super(JFloat, self).__init__()


class JLong(BaseType):
    def __init__(self):
        super(JLong, self).__init__()


class JDouble(BaseType):
    def __init__(self):
        super(JDouble, self).__init__()


class JString(BaseType):
    def __init__(self):
        super(JString, self).__init__()


# TODO: 感觉还是应该分一个包出去
class ClassLoader(object):
    default_loader = None

    def __init__(self):
        self._loading_classes = []
        self._loaded_classes = {}
        self.pkg_path = jdk_path
        self.hack()

    def get_all_loaded_class(self):
        return self._loading_classes

    def hack(self):
        # 先提前 load
        self.load_class('java/lang/Object')

    @staticmethod
    def default_class_loader():
        # TODO: 线程同步
        if ClassLoader.default_loader is None:
            ClassLoader.default_loader = ClassLoader()
        return ClassLoader.default_loader

    def add_path(self, path):
        self.pkg_path.append(path)

    # TODO: jar zip 处理
    def load_class(self, class_name):
        # TODO: load class 线程之间同步 暂时轮询
        if class_name in self._loading_classes:
            while True:
                if class_name not in self._loading_classes:
                    break
        if class_name in self._loaded_classes:
            return self._loaded_classes[class_name]
        jclass = self.__load_class(class_name)
        self._loading_classes.remove(class_name)
        return jclass

    def __load_class(self, class_name):
        self._loading_classes.append(class_name)
        if class_name[0] == '[':
            return self.__load_array_class(class_name)
        for path in self.pkg_path:
            class_path = path + class_name.replace('.', '/') + '.class'
            if not os.path.exists(class_path):
                continue
            print_utils.print_jvm_status('load class: ' + class_path)
            jclass = self.define_class(class_name, class_path)
            self._loaded_classes[class_name] = jclass
            return jclass
        return None

    def __load_array_class(self, class_name):
        jclass = JClass()
        jclass.super_class_name = 'java/lang/Object'
        jclass.class_loader = self
        jclass.has_inited = True
        jclass.name = class_name
        self._loaded_classes[class_name] = jclass

    def define_class(self, class_name, path):
        parser = ClassParser(path)
        parser.parse()
        jclass = JClass()
        jclass.name = class_name
        jclass.new_jclass(parser.class_file)
        jclass.super_class = self.load_super_class(jclass)
        return jclass

    def load_super_class(self, jclass):
        if jclass.super_class_name == 'java/lang/Object' or jclass.super_class_name is None:
            return
        return self.load_class(jclass.super_class_name)
