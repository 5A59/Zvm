# coding=utf-8


from base.utils import error_handler

DEF_LENGTH = 10


class Heap(object):
    __java_heap = []
    __index = 0  # 指向当前可用的位置
    __length = DEF_LENGTH

    @staticmethod
    def new_ref(ref):
        Heap.__new_ref(ref, True)

    @staticmethod
    def __new_ref(ref, retry):
        if Heap.__index >= Heap.__length:
            if retry:
                Heap.gc()
                Heap.__new_ref(ref, False)
            else:
                error_handler.rise_runtime_error('no heap space !!!')
        else:
            Heap.__java_heap[Heap.__index] = ref
            Heap.__index += 1

    @staticmethod
    def gc():
        pass
