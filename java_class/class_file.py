# coding=utf-8


def get_string_from_attribute_array(attrs):
    res = ''
    for attr in attrs:
        res += '{%s},' % attr
    return res


class ClassFile(object):
    def __init__(self):
        self.magic = None  # u4
        self.minor_version = None  # u2
        self.major_version = None  # u2
        self.constant_pool_count = None  # u2
        self.constant_pool = None  # cp_info
        self.access_flag = None  # u2
        self.this_class = None  # u2
        self.super_class = None  # u2
        self.interface_count = None  # u2
        self.interfaces = None  # u2
        self.fields_count = None  # u2
        self.fields = None  # field_info
        self.methods_count = None  # u2
        self.methods = None  # method_info
        self.attributes_count = None  # u2
        self.attributes = None  # attribute_info


class ConstantPoolBaseInfo(object):
    CONSTANT_CLASS = 7
    CONSTANT_FIELD_REF = 9
    CONSTANT_METHOD_REF = 10
    CONSTANT_INTERFACE_METHOD_REF = 11
    CONSTANT_STRING = 8
    CONSTANT_INTEGER = 3
    CONSTANT_FLOAT = 4
    CONSTANT_LONG = 5
    CONSTANT_DOUBLE = 6
    CONSTANT_NAME_AND_TYPE = 12
    CONSTANT_UTF_8 = 1
    CONSTANT_METHOD_HANDLE = 15
    CONSTANT_METHOD_TYPE = 16
    CONSTANT_INVOKE_DYNAMIC = 18

    def __init__(self):
        self.tag = None  # u1


class ClassInfo(ConstantPoolBaseInfo):
    def __init__(self):
        super(ClassInfo, self).__init__()
        self.tag = ConstantPoolBaseInfo.CONSTANT_CLASS
        self.name_index = None  # 对常量池的索引 索引项是 CONSTANT_UTF_8 eg.

    def __str__(self):
        return 'CONSTANT_CLASS{tag:%s, name_index: %s}' % (self.tag, self.name_index)

    @staticmethod
    def get_size():
        return 3


class RefInfo(ConstantPoolBaseInfo):
    def __init__(self):
        super(RefInfo, self).__init__()
        self.class_index = None  # u2 索引 class_info
        self.name_and_type_index = None  # u2 索引 name_and_type_info 表示字段或者方法的名字和描述符

    @staticmethod
    def get_size():
        return 5


class FieldRefInfo(RefInfo):
    def __init__(self):
        super(FieldRefInfo, self).__init__()
        self.tag = ConstantPoolBaseInfo.CONSTANT_FIELD_REF

    def __str__(self):
        return 'CONSTANT_FIELD_REF{tag:%s, name_and_type_index: %s}' % (self.tag, self.name_and_type_index)


class MethodRefInfo(RefInfo):
    def __init__(self):
        super(MethodRefInfo, self).__init__()
        self.tag = ConstantPoolBaseInfo.CONSTANT_METHOD_REF

    def __str__(self):
        return 'CONSTANT_METHOD_REF{tag:%s, name_and_type_index: %s}' % (self.tag, self.name_and_type_index)


class InterfaceMethodRefInfo(RefInfo):
    def __init__(self):
        super(InterfaceMethodRefInfo, self).__init__()
        self.tag = ConstantPoolBaseInfo.CONSTANT_INTERFACE_METHOD_REF

    def __str__(self):
        return 'CONSTANT_INTERFACE_METHOD_REF{tag:%s, name_and_type_index: %s}' % (self.tag, self.name_and_type_index)


class StringInfo(ConstantPoolBaseInfo):
    def __init__(self):
        super(StringInfo, self).__init__()
        self.tag = ConstantPoolBaseInfo.CONSTANT_STRING
        self.string_index = None  # 索引 utf8_info  表示一组 unicode 码点序列

    def __str__(self):
        return 'CONSTANT_STRING{tag:%s, string_index: %s}' % (self.tag, self.string_index)

    @staticmethod
    def get_size():
        return 3


class U4Info(ConstantPoolBaseInfo):
    def __init__(self):
        super(U4Info, self).__init__()
        self.bytes = None  # u4 big-endian

    @staticmethod
    def get_size():
        return 5


class IntegerInfo(U4Info):
    def __init__(self):
        super(IntegerInfo, self).__init__()
        self.tag = ConstantPoolBaseInfo.CONSTANT_INTEGER

    def __str__(self):
        return 'CONSTANT_INTEGER{tag:%s, bytes: %s}' % (self.tag, self.bytes)


class FloatInfo(U4Info):
    def __init__(self):
        super(FloatInfo, self).__init__()
        self.tag = ConstantPoolBaseInfo.CONSTANT_FLOAT

    def __str__(self):
        return 'CONSTANT_FLOAT{tag:%s, bytes: %s}' % (self.tag, self.bytes)


class U8Info(ConstantPoolBaseInfo):
    def __init__(self):
        super(U8Info, self).__init__()
        self.high_bytes = None  # u4
        self.low_bytes = None  # u4

    @staticmethod
    def get_size():
        return 9


class LongInfo(U8Info):
    def __init__(self):
        super(LongInfo, self).__init__()
        self.tag = ConstantPoolBaseInfo.CONSTANT_LONG

    def __str__(self):
        return 'CONSTANT_LONG{tag:%s, high_bytes: %s, low_bytes: %s}' % (self.tag, self.high_bytes, self.low_bytes)


class DoubleInfo(U8Info):
    def __init__(self):
        super(DoubleInfo, self).__init__()
        self.tag = ConstantPoolBaseInfo.CONSTANT_DOUBLE

    def __str__(self):
        return 'CONSTANT_DOUBLE{tag:%s, high_bytes: %s, low_bytes: %s}' % (self.tag, self.high_bytes, self.low_bytes)


class NameAndTypeInfo(ConstantPoolBaseInfo):
    def __init__(self):
        super(NameAndTypeInfo, self).__init__()
        self.tag = ConstantPoolBaseInfo.CONSTANT_NAME_AND_TYPE
        self.name_index = None  # u2 索引 名字
        self.descriptor_index = None  # u2 索引 描述符

    def __str__(self):
        return 'CONSTANT_NAME_AND_TYPE{tag:%s, name_index: %s, descriptor_index: %s}' \
               % (self.tag, self.name_index, self.descriptor_index)

    @staticmethod
    def get_size():
        return 5


class Utf8Info(ConstantPoolBaseInfo):
    def __init__(self):
        super(Utf8Info, self).__init__()
        self.tag = ConstantPoolBaseInfo.CONSTANT_UTF_8
        self.length = None  # u2
        self.bytes = None  # bytes[length]

    def __str__(self):
        return 'CONSTANT_UTF_8{tag:%s, length: %s, bytes: %s}' % (self.tag, self.length, self.bytes)

    def get_size(self):
        return self.length + 3


class MethodHandleInfo(ConstantPoolBaseInfo):
    def __init__(self):
        super(MethodHandleInfo, self).__init__()
        self.tag = ConstantPoolBaseInfo.CONSTANT_METHOD_HANDLE
        self.reference_kind = None  # u1 方法句柄类型
        self.reference_index = None  # u2 索引

    def __str__(self):
        return 'CONSTANT_UTF_8{tag:%s, reference_kind: %s, : reference_index%s}' \
               % (self.tag, self.reference_kind, self.reference_index)

    @staticmethod
    def get_size():
        return 4


class MethodTypeInfo(ConstantPoolBaseInfo):
    def __init__(self):
        super(MethodTypeInfo, self).__init__()
        self.tag = ConstantPoolBaseInfo.CONSTANT_METHOD_TYPE
        self.descriptor_index = None  # 索引 方法描述符

    def __str__(self):
        return 'CONSTANT_METHOD_TYPE{tag:%s, descriptor_index: %s' % (self.tag, self.descriptor_index)

    @staticmethod
    def get_size():
        return 3


class InvokeDynamicInfo(ConstantPoolBaseInfo):
    def __init__(self):
        super(InvokeDynamicInfo, self).__init__()
        self.tag = ConstantPoolBaseInfo.CONSTANT_INVOKE_DYNAMIC
        self.bootstrap_method_attr_index = None  # u2 引导方法表索引
        self.name_and_type_index = None  # u2 索引

    def __str__(self):
        return 'CONSTANT_INVOKE_DYNAMIC{tag:%s, bootstrap_method_attr_index: %s, name_and_type_index: %s' \
               % (self.tag, self.bootstrap_method_attr_index, self.name_and_type_index)

    @staticmethod
    def get_size():
        return 5


class FieldInfo(object):
    def __init__(self):
        self.access_flags = None  # u2
        self.name_index = None  # u2
        self.descriptor_index = None  # u2
        self.attributes_count = None  # u2
        self.attributes = None  # attribute_info

    def __str__(self):
        return 'Field{access_flags: %s, name_index: %s, descriptor_index: %s, attributes_count: %s, attributes: %s}' \
               % (self.access_flags, self.name_index, self.descriptor_index, self.attributes_count,
                  get_string_from_attribute_array(self.attributes))


class MethodInfo(object):
    def __init__(self):
        self.access_flags = None  # u2
        self.name_index = None  # u2  常量池索引 utf8_info
        self.descriptor_index = None  # u2  常量池索引 utf8_info
        self.attributes_count = None  # u2
        self.attributes = None  # attribute_info

    def __str__(self):
        return 'METHOD_INFO{access_flag: %s, name_index: %s, descriptor_index: %s, ' \
               'attributes_count: %s, attributes: %s}' \
               % (self.access_flags, self.name_index, self.descriptor_index, self.attributes_count,
                  get_string_from_attribute_array(self.attributes))


class BaseAttribute(object):
    ATTR_CONSTANT_VALUE = 'ConstantValue'
    ATTR_CODE = 'Code'
    ATTR_SOURCE_FILE = 'SourceFile'

    def __init__(self):
        self.attribute_name_index = None  # u2  对常量池的索引 utf8_info
        self.attribute_length = None  # u4


class ConstantValueAttribute(BaseAttribute):
    def __init__(self):
        super(ConstantValueAttribute, self).__init__()
        self.attribute_length = 2
        self.constant_value_index = None  # u2 对常量池的索引

    def __str__(self):
        return 'CONSTANT_VALUE_ATTR{attribute_name_index: %s, attribute_length: %s, constant_value_index: %s' \
               % (self.attribute_name_index, self.attribute_length, self.constant_value_index)


class ExceptionTable(object):
    def __init__(self):
        self.start_pc = None  # u2
        self.end_pc = None  # u2  异常处理器在 code[] 中的有效范围  end_pc 本身不属于异常处理器范围
        self.handler_pc = None  # u2 异常处理器的起点
        self.catch_type = None  # u2  对常量池的索引，CONSTANT_CLASS_INFO 指定异常的类型


class CodeAttribute(BaseAttribute):
    def __init__(self):
        super(CodeAttribute, self).__init__()
        self.max_stack = None  # u2
        self.max_locals = None  # u2
        self.code_length = None  # u4
        self.code = None  # u1 长度 code_length
        self.exception_table_length = None  # u2
        self.exception_table = None  # exception_table_length ExceptionTable
        self.attributes_count = None  # u2
        self.attributes = None

    def __str__(self):
        return 'CODE_ATTR{max_stack: %s, max_locals: %s, code_length: %s, ' \
               'code: %s, exception_table_length: %s, exception_table: %s, ' \
               'attributes_count: %s, attributes: %s}' \
               % (self.max_locals, self.max_locals, self.code_length, self.code,
                  self.exception_table_length, self.exception_table, self.attributes_count,
                  get_string_from_attribute_array(self.attributes))


class SourceFileAttribute(BaseAttribute):
    def __init__(self):
        super(SourceFileAttribute, self).__init__()
        self.sourcefile_index = None  # u2 常量池索引，utf8_info  class 文件源文件名字，不包括目录

    def __str__(self):
        return 'SOURCE_FILE_ATTR{sourcefile_index: %s}' % self.sourcefile_index
