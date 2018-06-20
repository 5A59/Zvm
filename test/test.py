# coding=utf-8

from runtime.jclass import ClassLoader
from runtime.jclass import JClass
from interpreter import interpreter


def main():
    loader = ClassLoader()
    j_class = loader.load_class('Hello')
    print(j_class)
    method = j_class.get_main_method()
    interpreter.Interpreter.exec_method(method)

if __name__ == '__main__':
    main()
