# coding=utf-8

from runtime.thread import Slot
from base.utils import error_handler


# 对应 java 中的实例对象
class JObject(object):
    TYPE_OBJ = 0
    TYPE_ARRAY = 1

    def __init__(self):
        self.type = JObject.TYPE_OBJ
        self.jclass = None
        self.data = None  # 在 JObject 是map，在 JAarry 里面是 Slot 数组

    @staticmethod
    def new_object(jclass):
        jobject = JObject()
        jobject.jclass = jclass
        jobject.data = {}
        for field in jobject.jclass.get_instance_fields():
            desc = field.descriptor
            slot = Slot()
            if desc == 'B' or desc == 'I' or desc == 'J' or desc == 'S' or desc == 'Z':
                slot.num = 0
            elif desc == 'C':
                slot.num = '0'
            elif desc == 'F':
                slot.num = 0.0
            elif desc == 'D':
                slot.num = 0.0
            jobject.data[field.name] = slot
        return jobject

    def get_field(self, name):
        self.__check_name(name)
        slot = self.data[name]
        if slot.num is not None:
            return slot.num
        return slot.ref

    def put_field(self, name, num):
        self.__check_name(name)
        self.data[name].num = num

    def put_ref_field(self, name, ref):
        self.__check_name(name)
        self.data[name].ref = ref

    def __check_name(self, name):
        if name not in self.data:
            error_handler.rise_runtime_error('no this field')


# 指向实例对象
# 实例对象保存在 gc 堆中，ref 指向实例对象
class JRef(object):
    def __init__(self, obj):
        self.handler = JHandler(obj)

    @staticmethod
    def new_object(jclass):
        # TODO: obj 放入 gc 堆
        obj = JObject.new_object(jclass)
        jref = JRef(obj)
        return jref

    @staticmethod
    def new_array(jclass, atype, count):
        array = JArray.new_array(jclass, atype, count)
        jref = JRef(array)
        return jref

    @staticmethod
    def new_ref_array(jclass, type_class_ref, count):
        array = JArray.new_ref_array(jclass, type_class_ref, count)
        jref = JRef(array)
        return jref

    def clone(self):
        return JRef(self.handler.obj)


# 方便 gc
class JHandler(object):
    def __init__(self, obj):
        self.obj = obj


class JArray(JObject):
    T_BOOLEAN = 4
    T_CHAR = 5
    T_FLOAT = 6
    T_DOUBLE = 7
    T_BYTE = 8
    T_SHORT = 9
    T_INT = 10
    T_LONG = 11

    T_REF = 100

    def __init__(self):
        super(JArray, self).__init__()
        self.atype = None
        self.length = 0
        self.descriptor = ''

    def add_item(self, index, item):
        self.__check_index(index)
        self.data[index].num = item

    def add_ref_item(self, index, item):
        self.__check_index(index)
        self.data[index].ref = item

    def get_item(self, index):
        self.__check_index(index)
        slot = self.data[index]
        if slot.num is not None:
            return slot.num
        return slot.ref

    def __check_index(self, index):
        if index >= self.length:
            error_handler.rise_runtime_error('index out of bounds')

    @staticmethod
    def get_array_jclass_name(atype):
        if atype == JArray.T_BOOLEAN:
            return '[Z'
        elif atype == JArray.T_CHAR:
            return '[C'
        elif atype == JArray.T_FLOAT:
            return '[F'
        elif atype == JArray.T_DOUBLE:
            return '[D'
        elif atype == JArray.T_BYTE:
            return '[B'
        elif atype == JArray.T_SHORT:
            return '[S'
        elif atype == JArray.T_INT:
            return '[I'
        elif atype == JArray.T_LONG:
            return '[J'
        return ''

    @staticmethod
    def get_ref_array_jclass_name(ref_desc):
        return '[' + ref_desc

    @staticmethod
    def new_array(jclass, atype, length):
        jarray = JArray()
        jarray.jclass = jclass
        jarray.length = length
        jarray.atype = atype
        jarray.descriptor = JArray.get_array_jclass_name(atype)
        jarray.data = []
        for i in range(length):
            jarray.data.append(Slot())
        return jarray

    @staticmethod
    def new_ref_array(jclass, type_class_ref, length):
        jarray = JArray()
        jarray.jclass = jclass
        jarray.length = length
        jarray.atype = JArray.T_REF
        jarray.descriptor = JArray.get_ref_array_jclass_name(type_class_ref.class_name)
        jarray.data = []
        for i in range(length):
            jarray.data.append(Slot())
        return jarray
