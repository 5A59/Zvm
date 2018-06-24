# coding=utf-8

from base.utils import print_utils
from runtime.thread import Thread
import runtime

import threading


class GC(object):
    __gc_lock = threading.RLock()

    @staticmethod
    def check_gc():  # gc 的时候要暂停所有线程
        GC.__gc_lock.acquire()
        GC.__gc_lock.release()

    @staticmethod
    def start_gc(heap, static_fields):
        print_utils.print_jvm_status("!!!!!! start gc !!!!!!")
        GC.__gc_lock.acquire()
        return GCHandler.start_gc(heap, static_fields)

    @staticmethod
    def stop_gc():
        GC.__gc_lock.release()


class GCHandler(object):

    @staticmethod
    def start_gc(heap, static_fields):
        alive_obj = GCHandler.collect_alive_ref(static_fields)
        alive_list = []
        index = 0
        for ref in heap:
            if ref in alive_obj:
                alive_list.append(index)
            index += 1
        for i in range(len(heap)):
            if i not in alive_list:
                heap[i].handler = None
        for i in range(len(alive_list)):
            heap[i] = heap[alive_list[i]]
        return len(alive_list)

    @staticmethod
    def collect_alive_ref(static_fields):
        # TODO: gc root 目前只收集了 heap 中的对象 和 static
        roots = GCHandler.collect_root()
        roots.extend(static_fields)
        alive_obj = []
        for root in roots:
            obj = root.handler.obj
            alive_obj.append(root)
            if obj.type == runtime.jobject.JObject.TYPE_OBJ:
                GCHandler.collect_obj_ref(root, alive_obj)
            elif obj.type == runtime.jobject.JObject.TYPE_ARRAY:
                GCHandler.collect_array_ref(root, alive_obj)
        return alive_obj

    @staticmethod
    def collect_obj_ref(ref, alive_obj):
        obj = ref.handler.obj
        for o in obj.data.values():
            if isinstance(o, runtime.jobject.JRef):
                alive_obj.append(o)
                GCHandler.collect_obj_ref(o, alive_obj)

    @staticmethod
    def collect_array_ref(ref, alive_obj):
        array = ref.handler.obj
        if array.atype == runtime.jobject.JArray.T_REF:
            for slot in array.data:
                aref = slot.ref
                if aref is not None:
                    GCHandler.collect_obj_ref(aref, alive_obj)

    @staticmethod
    def collect_root():
        thread_pool = Thread.all_thread()
        gc_root = []
        for thread in thread_pool:
            frames = thread.all_frames()
            for frame in frames:
                items = frame.operand_stack.get_all_data()
                for item in items:
                    if isinstance(item.data, runtime.jobject.JRef):
                        gc_root.append(item.data)
                vars = frame.local_vars.get_items()
                for var in vars:
                    if isinstance(var.ref, runtime.jobject.JRef):
                        gc_root.append(var.ref)
        return gc_root


