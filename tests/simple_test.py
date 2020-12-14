from pymargo.core import Engine

if __name__ == '__main__':
    with Engine('ofi+tcp') as engine:
        engine.finalize()

    print('Hello World')
