from flask import Flask
# 导入数据库扩展
from flask_sqlalchemy import SQLAlchemy
#导入配置文件
from config import  config_dict
#导入扩展包 flask_session session初始化
from flask_session import Session

#实例化sqlalchemy对象
db = SQLAlchemy()

#定义函数，工厂函数，用来生产app，通过传入的参数的不同，可以生产不同配置环境的app
def create_app(config_name):
        from info.modules.index import index_blue  #导入蓝图

        app=Flask(__name__)
        #使用配置对象
        app.register_blueprint(index_blue)   #注册蓝图
        app.config.from_object(config_dict[config_name])
        #通过函数来让db和app进行关联
        db.init_app(app)
        #Session 初始化
        Session(app)

        return app