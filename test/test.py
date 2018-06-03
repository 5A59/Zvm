# coding=utf-8

from runtime.jclass import ClassLoader
from runtime.jclass import JClass
from interpreter import interpreter


def main():
    loader = ClassLoader()
    j_class = loader.load_class('Hello')
    print(j_class)
    method = j_class.get_main_method()
    m_interpreter = interpreter.Interpreter()
    m_interpreter.run(method)

if __name__ == '__main__':
    main()
