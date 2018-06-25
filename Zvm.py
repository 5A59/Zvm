# coding=utf-8

import path_import
import sys

from runtime.jclass import ClassLoader
from interpreter import interpreter


def parse_params():
    args = sys.argv
    if len(args) <= 1:
        print('use: python Zvm.py xx[.class]')
        print('eg: python Zvm.py main')
        print('eg: python Zvm.py main.class')
        return None
    name = sys.argv[1]
    if name.endswith('.class'):
        name = name[:name.find('.class')]
    return name


def main():
    class_file = parse_params()
    if class_file is None:
        return
    loader = ClassLoader()
    j_class = loader.load_class(class_file)
    print(j_class)
    method = j_class.get_main_method()
    interpreter.Interpreter.exec_method(method)


if __name__ == '__main__':
    main()
