# coding=utf-8

import os

log_jvm_status = False
# log_jvm_status = True

print_in_real_time = True

cur_path = os.getcwd()
jdk_path = [cur_path + '/', cur_path + '/test/']

heap_size = 11  # 这个是按 ref 个数模拟的 gc，不是真实的 size
