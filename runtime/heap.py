# coding=utf-8


from base.utils import error_handler
from jgc.gc import GC
from base.jvm_config import heap_size

DEF_LENGTH = heap_size


class Heap(object):
    _java_heap = [None for i in range(DEF_LENGTH)]
    _index = 0  # 指向当前可用的位置
    _length = DEF_LENGTH
    _jclass_heap = []

    @staticmethod
    def new_jclass(jclass):
        Heap._jclass_heap.append(jclass)

    @staticmethod
    def new_ref(ref):
        Heap.__new_ref(ref, True)

    @staticmethod
    def __new_ref(ref, retry):
        if Heap._index >= Heap._length:
            if retry:
                Heap.gc()
                Heap.__new_ref(ref, False)
            else:
                error_handler.rise_runtime_error('no heap space !!!')
        else:
            Heap._java_heap[Heap._index] = ref
            Heap._index += 1

    @staticmethod
    def collect_static_field():
        static_fields = []
        for jclass in Heap._jclass_heap:
            fields = jclass.static_fields
            for slot in fields.values():
                if slot.ref is not None:
                    static_fields.append(slot.ref)
        return static_fields

    @staticmethod
    def gc():
        Heap._index = GC.start_gc(Heap._java_heap, Heap.collect_static_field())


if __name__ == '__main__':
    Heap.gc()

