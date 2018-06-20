# coding=utf-8

from runtime.heap import Heap
from runtime.thread import Thread
from runtime.jobject import JRef

import threading


class GC(object):
    __gc_lock = threading.RLock()

    @staticmethod
    def check_gc():  # gc 的时候要暂停所有线程
        GC.__gc_lock.acquire()
        GC.__gc_lock.release()

    @staticmethod
    def start_gc():
        GC.__gc_lock.acquire()

    @staticmethod
    def stop_gc():
        GC.__gc_lock.release()


class GCHandler(object):

    def start_gc(self):
        pass

    def collect_root(self):
        thread_pool = Thread.all_thread()
        gc_root = []
        for thread in thread_pool:
            frames = thread.all_frames()
            for frame in frames:
                items = frame.operand_stack.get_all_data
                for item in items:
                    if isinstance(item, JRef):
                        gc_root.append(item)
        return gc_root


