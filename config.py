import os

basedir = os.path.abspath(os.path.dirname(__file__))


def get_execdata_binds():
    N_APP_MPI = os.environ.get('N_APP_MPI', 5)
    EXECDATA_URI_PREFIX = os.environ.get(
        'EXECDATA_URI_PREFIX',
        'sqlite:///' + os.path.join(basedir, 'execdata')
    )
    execdata_binds = {}
    for i in range(N_APP_MPI):
        db_uri = "{}-{}.sqlite".format(EXECDATA_URI_PREFIX, i)
        execdata_binds["execdata-{}".format(i)] = db_uri
    return execdata_binds


class Config(object):
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY',
                                '51f52814-0071-11e6-a2477-000ec6c2372c')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 'sqlite:///' + os.path.join(basedir, '/tests/test/main.sqlite'))
    SQLALCHEMY_BINDS = {
        'anomaly_stats_query': os.environ.get(
            'DATABASE_URL',
            'sqlite:///' + os.path.join(basedir, '/tests/test/anomaly_query.sqlite')),
        'anomaly_stats': os.environ.get(
            'ANOMALY_STATS_URL',
            'sqlite:///' + os.path.join(basedir, '/tests/test/anomaly_stats.sqlite')),
        'anomaly_data': os.environ.get(
            'ANOMALY_DATA_URL',
            'sqlite:///' + os.path.join(basedir, '/tests/test/anomaly_data.sqlite')),
        'func_stats': os.environ.get(
            'FUNC_STATS_URL',
            'sqlite:///' + os.path.join(basedir, '/tests/test/func_stats.sqlite')
        )
    }
    # SQLALCHEMY_BINDS.update(get_execdata_binds())

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REQUEST_STATS_WINDOW = 15
    CELERY_CONFIG = {}
    SOCKETIO_MESSAGE_QUEUE = os.environ.get(
        'SOCKETIO_MESSAGE_QUEUE',
        os.environ.get('CELERY_BROKER_URL', 'redis://')
    )
    # EXECUTION_PATH = os.environ.get('EXECUTION_PATH', None)


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    pass


class TestingConfig(Config):
    """For test, I need to first launch redis and celery."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, '/tests/test/db.sqlite')
    CELERY_CONFIG = {'CELERY_ALWAYS_EAGER': True}
    SOCKETIO_MESSAGE_QUEUE = None


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}
