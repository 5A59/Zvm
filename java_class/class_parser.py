# coding=utf-8

from java_class.class_file import *
from base.utils import common_utils


class ClassReader:
    def __init__(self, path):
        self.path = path
        with open(self.path, 'rb') as f:
            self.array = bytearray(f.read())
        self.index = 0

    def read_b1(self):
        res = self.array[self.index]
        self.index += 1
        return res

    def read_b2(self):
        res = self.array[self.index: self.index + 2]
        self.index += 2
        return res

    def read_b4(self):
        res = self.array[self.index: self.index + 4]
        self.index += 4
        return res

    def read_bn(self, length):
        res = self.array[self.index: self.index + length]
        self.index += length
        return res


# TODO: class 格式校验
class ClassParser:
    def __init__(self, path):
        self.reader = ClassReader(path)
        self.class_file = ClassFile()

    def read_magic(self):
        self.class_file.magic = self.reader.read_b4()

    def read_minor_version(self):
        self.class_file.minor_version = self.reader.read_b2()

    def read_major_version(self):
        self.class_file.major_version = self.reader.read_b2()

    def read_constant_pool_count(self):
        self.class_file.constant_pool_count = self.reader.read_b2()

    def read_constant_pool(self):
        constant_pool = [None]  # constant_pool 第 0 个元素无用
        for i in range(common_utils.get_int_from_bytes(self.class_file.constant_pool_count) - 1):
            info = None
            tag = self.reader.read_b1()
            if tag == ConstantPoolBaseInfo.CONSTANT_CLASS:
                info = ClassInfo()
                info.tag = tag
                info.name_index = self.reader.read_b2()
            elif tag == ConstantPoolBaseInfo.CONSTANT_FIELD_REF:
                info = FieldRefInfo()
                info.tag = tag
                info.class_index = self.reader.read_b2()
                info.name_and_type_index = self.reader.read_b2()
            elif tag == ConstantPoolBaseInfo.CONSTANT_METHOD_REF:
                info = MethodRefInfo()
                info.tag = tag
                info.class_index = self.reader.read_b2()
                info.name_and_type_index = self.reader.read_b2()
            elif tag == ConstantPoolBaseInfo.CONSTANT_INTERFACE_METHOD_REF:
                info = InterfaceMethodRefInfo()
                info.tag = tag
                info.class_index = self.reader.read_b2()
                info.name_and_type_index = self.reader.read_b2()
            elif tag == ConstantPoolBaseInfo.CONSTANT_STRING:
                info = StringInfo()
                info.tag = tag
                info.string_index = self.reader.read_b2()
            elif tag == ConstantPoolBaseInfo.CONSTANT_INTEGER:
                info = IntegerInfo()
                info.tag = tag
                info.bytes = self.reader.read_b4()
            elif tag == ConstantPoolBaseInfo.CONSTANT_FLOAT:
                info = FloatInfo()
                info.tag = tag
                info.bytes = self.reader.read_b4()
            elif tag == ConstantPoolBaseInfo.CONSTANT_LONG:
                info = LongInfo()
                info.tag = tag
                info.high_bytes = self.reader.read_b4()
                info.low_bytes = self.reader.read_b4()
            elif tag == ConstantPoolBaseInfo.CONSTANT_DOUBLE:
                info = DoubleInfo()
                info.tag = tag
                info.high_bytes = self.reader.read_b4()
                info.low_bytes = self.reader.read_b4()
            elif tag == ConstantPoolBaseInfo.CONSTANT_NAME_AND_TYPE:
                info = NameAndTypeInfo()
                info.tag = tag
                info.name_index = self.reader.read_b2()
                info.descriptor_index = self.reader.read_b2()
            elif tag == ConstantPoolBaseInfo.CONSTANT_UTF_8:
                info = Utf8Info()
                info.tag = tag
                info.length = self.reader.read_b2()
                info.bytes = self.reader.read_bn(common_utils.get_int_from_bytes(info.length))
            elif tag == ConstantPoolBaseInfo.CONSTANT_METHOD_HANDLE:
                info = MethodHandleInfo()
                info.tag = tag
                info.reference_kind = self.reader.read_b1()
                info.reference_index = self.reader.read_b2()
            elif tag == ConstantPoolBaseInfo.CONSTANT_METHOD_TYPE:
                info = MethodTypeInfo()
                info.tag = tag
                info.descriptor_index = self.reader.read_b2()
            elif tag == ConstantPoolBaseInfo.CONSTANT_INVOKE_DYNAMIC:
                info = InvokeDynamicInfo()
                info.tag = tag
                info.bootstrap_method_attr_index = self.reader.read_b2()
                info.name_and_type_index = self.reader.read_b2()

            if info is not None:
                constant_pool.append(info)
            self.class_file.constant_pool = constant_pool

    def read_access_flags(self):
        self.class_file.access_flag = self.reader.read_b2()

    def read_this_class(self):
        self.class_file.this_class = self.reader.read_b2()

    def read_super_class(self):
        self.class_file.super_class = self.reader.read_b2()

    def read_interfaces_count(self):
        self.class_file.interface_count = self.reader.read_b2()

    def read_interfaces(self):
        tmp_class_file = self.class_file
        interfaces = []
        for i in range(common_utils.get_int_from_bytes(tmp_class_file.interface_count)):
            interfaces.append(self.reader.read_b2())
        tmp_class_file.interfaces = interfaces

    def read_fields_count(self):
        self.class_file.fields_count = self.reader.read_b2()

    def read_fields(self):
        tmp_class_file = self.class_file
        fields = []
        for i in range(common_utils.get_int_from_bytes(tmp_class_file.fields_count)):
            field = FieldInfo()
            field.access_flags = self.reader.read_b2()
            field.name_index = self.reader.read_b2()
            field.descriptor_index = self.reader.read_b2()
            field.attributes_count = self.reader.read_b2()
            field.attributes = self.read_attributes_(common_utils.get_int_from_bytes(field.attributes_count))
            fields.append(field)
        tmp_class_file.fields = fields

    def read_methods_count(self):
        self.class_file.methods_count = self.reader.read_b2()

    def read_methods(self):
        tmp_class = self.class_file
        methods = []
        for i in range(common_utils.get_int_from_bytes(self.class_file.methods_count)):
            method = MethodInfo()
            method.access_flags = self.reader.read_b2()
            method.name_index = self.reader.read_b2()
            method.descriptor_index = self.reader.read_b2()
            method.attributes_count = self.reader.read_b2()
            method.attributes = self.read_attributes_(common_utils.get_int_from_bytes(method.attributes_count))
            methods.append(method)
        tmp_class.methods = methods

    def read_attributes_count(self):
        self.class_file.attributes_count = self.reader.read_b2()

    def read_attributes(self):
        self.class_file.attributes = self.read_attributes_(
            common_utils.get_int_from_bytes(self.class_file.attributes_count))

    def read_attributes_(self, attributes_count):
        tmp_class = self.class_file
        attributes = []
        for i in range(attributes_count):
            attribute_name_index = self.reader.read_b2()
            attribute_length = self.reader.read_b4()
            attr_name = tmp_class.constant_pool[common_utils.get_int_from_bytes(attribute_name_index)]
            attr_name = common_utils.get_string_from_bytes(attr_name.bytes)
            if attr_name == BaseAttribute.ATTR_CONSTANT_VALUE:
                attr = ConstantValueAttribute()
                attr.attribute_name_index = attribute_name_index
                attr.attribute_length = attribute_length
                attr.constant_value_index = self.reader.read_b2()
                attributes.append(attr)
            elif attr_name == BaseAttribute.ATTR_CODE:
                attr = CodeAttribute()
                attr.attribute_name_index = attribute_name_index
                attr.attribute_length = attribute_length
                attr.max_stack = self.reader.read_b2()
                attr.max_locals = self.reader.read_b2()
                attr.code_length = self.reader.read_b4()
                attr.code = self.reader.read_bn(common_utils.get_int_from_bytes(attr.code_length))
                attr.exception_table_length = self.reader.read_b2()
                attr.exception_table = self.read_exception_table(
                    common_utils.get_int_from_bytes(attr.exception_table_length))
                attr.attributes_count = self.reader.read_b2()
                attr.attributes = self.read_attributes_(common_utils.get_int_from_bytes(attr.attributes_count))
                attributes.append(attr)
            elif attr_name == BaseAttribute.ATTR_SOURCE_FILE:
                attr = SourceFileAttribute()
                attr.attribute_name_index = attribute_name_index
                attr.attribute_length = attribute_length
                attr.sourcefile_index = self.reader.read_b2()
                attributes.append(attr)
            else:  # 不认识的属性跳过
                self.reader.read_bn(common_utils.get_int_from_bytes(attribute_length))
        return attributes

    def read_exception_table(self, length):
        exceptions = []
        for i in range(length):
            ex = ExceptionTable()
            ex.start_pc = self.reader.read_b2()
            ex.end_pc = self.reader.read_b2()
            ex.handler_pc = self.reader.read_b2()
            ex.catch_type = self.reader.read_b2()
            exceptions.append(ex)
        return exceptions

    def parse(self):
        self.read_magic()
        self.read_minor_version()
        self.read_major_version()
        self.read_constant_pool_count()
        self.read_constant_pool()
        self.read_access_flags()
        self.read_this_class()
        self.read_super_class()
        self.read_interfaces_count()
        self.read_interfaces()
        self.read_fields_count()
        self.read_fields()
        self.read_methods_count()
        self.read_methods()
        self.read_attributes_count()
        self.read_attributes()

    def __str__(self):
        tmp_class = self.class_file
        return "magic: %s, minor_version: %s" % (tmp_class.magic, tmp_class.minor_version)


if __name__ == '__main__':
    parser = ClassParser('../test/Hello.class')
    parser.parse()
    clf = parser.class_file
    print('========= magic =========')
    print(parser.class_file.magic)
    print('========= minor =========')
    print(common_utils.get_int_from_bytes(clf.minor_version))
    print('========= major =========')
    print(common_utils.get_int_from_bytes(clf.major_version))
    print('========= constant_pool =========')
    constant_pool_count = clf.constant_pool_count
    pools = clf.constant_pool
    for i in range(common_utils.get_int_from_bytes(constant_pool_count) - 1):
        pool = pools[i]
        print(pool)
    print('========= class =========')
    print(common_utils.get_int_from_bytes(clf.access_flag))
    print(clf.this_class)
    print(clf.super_class)
    print('========= interface =========')
    print(clf.interface_count)
    for i in range(common_utils.get_int_from_bytes(clf.interface_count)):
        print(clf.interfaces[i])
    print('========= fields =========')
    print(common_utils.get_int_from_bytes(clf.fields_count))
    for i in range(common_utils.get_int_from_bytes(clf.fields_count)):
        print(clf.fields[i])
    print('========= methods =========')
    print(common_utils.get_int_from_bytes(clf.methods_count))
    for i in range(common_utils.get_int_from_bytes(clf.methods_count)):
        print(clf.methods[i])
    print('========= attributes =========')
    print(common_utils.get_int_from_bytes(clf.attributes_count))
    for i in range(common_utils.get_int_from_bytes(clf.attributes_count)):
        print(clf.attributes[i])

