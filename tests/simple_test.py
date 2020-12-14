from pymargo.core import Engine

if __name__ == '__main__':
    with Engine('na+sm') as engine:
        engine.finalize()

    print('Hello World')
