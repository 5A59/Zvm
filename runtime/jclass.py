# coding=utf-8

from base.utils import common_utils, print_utils
from java_class.class_file import *
from java_class.class_parser import ClassParser
# from runtime.class_loader import ClassLoader

import os


# 对应 java 中的 Class
class JClass(object):
    def __init__(self):
        self.access_flag = None
        self.super_class = None  # JClass
        self.interfaces = None
        self.fields = None
        self.methods = None
        self.constant_pool = None

    def new_jclass(self, class_file):
        self.access_flag = common_utils.get_int_from_bytes(class_file.access_flag)
        self.super_class = None  # 从方法区取
        self.constant_pool = ConstantPool.new_constant_pool(class_file)
        self.fields = Field.new_fields(class_file.fields, self.constant_pool.constants)
        self.methods = Method.new_methods(self, class_file.methods, self.constant_pool.constants)
        self.interfaces = None

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
                constants.append(st)
            elif isinstance(cp, IntegerInfo):
                constants.append(common_utils.get_int_from_bytes(cp.bytes))
            elif isinstance(cp, FloatInfo):
                constants.append(common_utils.get_float_from_bytes(cp.bytes))
            elif isinstance(cp, LongInfo):
                constants.append(common_utils.get_double_from_bytes(cp.high_bytes, cp.low_bytes))
                constants.append(None)
            elif isinstance(cp, DoubleInfo):
                constants.append(common_utils.get_double_from_bytes(cp.high_bytes, cp.low_bytes))
                constants.append(None)
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
        self.constant_value_index = None
        self.signature = None  # 记录范型变量
        self.type = None  # JClass

    @staticmethod
    def new_fields(cf_fields, constant_pool):
        fields = []
        for f in cf_fields:
            nf = Field()
            nf.access_flag = common_utils.get_int_from_bytes(f.access_flags)
            nf.name = constant_pool[common_utils.get_int_from_bytes(f.name_index)]
            nf.descriptor = constant_pool[common_utils.get_int_from_bytes(f.descriptor_index)]
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
            nm.exceptions = attr.exception_table
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




class Ref(object):
    def __init__(self):
        self.cp = None
        self.class_name = None
        self.cache_class = None  # JClass


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

    @staticmethod
    def get_string(cp, index_byte):
        return common_utils.get_string_from_bytes(cp[common_utils.get_int_from_bytes(index_byte)].bytes)

    @staticmethod
    def get_obj(cp, index_byte):
        return cp[common_utils.get_int_from_bytes(index_byte)]


class FieldRef(MemberRef):
    def __init__(self):
        super(FieldRef, self).__init__()
        self.field = None

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

    def resolve_class(self):
        if self.cache_class is not None:
            return self.cache_class
        class_loader = ClassLoader.default_class_loader()
        self.cache_class = class_loader.load_class(self.class_name)
        return self.cache_class

    # TODO: 函数处理
    def resolve_method(self):
        if self.method is not None:
            return self.method
        if self.cache_class is None:
            self.resolve_class()
        methods = self.cache_class.methods
        for m in methods:
            if m.name == self.name:
                self.method = m
                break
        return self.method


# TODO: 感觉还是应该分一个包出去
class ClassLoader(object):
    def __init__(self):
        self.__loaded_classes = {}
        self.pkg_path = ['./']

    @staticmethod
    def default_class_loader():
        return ClassLoader()

    def add_path(self, path):
        self.pkg_path.append(path)

    # TODO: jar zip 处理
    def load_class(self, class_name):
        if class_name in self.__loaded_classes:
            return self.__loaded_classes[class_name]
        return self.__load_class(class_name)

    def __load_class(self, class_name):
        for path in self.pkg_path:
            class_path = path + class_name.replace('.', '/') + '.class'
            if not os.path.exists(class_path):
                continue
            print_utils.print_msg('load class: ' + class_path)
            jclass = self.define_class(class_path)
            self.__loaded_classes[class_name] = jclass
            return jclass
        return None

    def define_class(self, path):
        parser = ClassParser(path)
        parser.parse()
        jclass = JClass()
        jclass.new_jclass(parser.class_file)
        return jclass
