# coding=utf-8


# 对应 java 中的实例对象
class JObject(object):
    def __init__(self):
        self.jclass = None
        self.fields = None

    def new_object(self, jclass):
        self.jclass = jclass
