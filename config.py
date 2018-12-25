#导入redis
from redis import StrictRedis

class Config():
    DEBUG=None
    SECRET_KEY = 'OdDaeav4qMrfLtuRb6hWolkyC5UgB9HvyhiAWccLTuJYfoOJOhLJ+Q=='     #配置密钥
    SESSION_TYPE= 'redis'                                                                          # 指定session类型为redis
    REDIS_HOST='127.0.0.1'
    REDIS_PORT=6379
    SESSION_REDIS= StrictRedis(host=REDIS_HOST, port=REDIS_PORT)         # 连接redis
    SESSION_USE_SIGNER = True                                                               #是否对发送到浏览器上session的cookie值进行加密
    PERMANPERMANPERMANENT_SESSION_LIFETIME= 86400

    SQLALCHEMY_DATABASE_URI = 'mysql://hmlhc:mysql@localhost/lhc_info'                       # 配置数据库的连接和动态追踪修改
    SQLALCHEMY_TRACK_MODIFICATIONS=False

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config_dict={
        'development':DevelopmentConfig,
        'production':ProductionConfig
}