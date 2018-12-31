from flask import Flask
# 导入数据库扩展
from flask_sqlalchemy import SQLAlchemy
#导入配置文件
from config import  config_dict,Config
#导入扩展包 flask_session session初始化
from flask_session import Session
# 开启csrf的保护,使用wtf扩展包
from flask_wtf import CSRFProtect,csrf
import logging
from logging.handlers import  RotatingFileHandler
from redis import StrictRedis

# 设置日志的记录等级
logging.basicConfig(level=logging.DEBUG) # 调试debug级
# 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024*1024*30, backupCount=10)
# 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
# 为刚创建的日志记录器设置日志记录格式
file_log_handler.setFormatter(formatter)
# 为全局的日志工具对象（flask app使用的）添加日志记录器
logging.getLogger().addHandler(file_log_handler)

#实例化sqlalchemy对象
db = SQLAlchemy()
#实例化redis对象，用来存储和业务相关的数据，例如验证码
redis_store=StrictRedis(host=Config.REDIS_HOST,port=Config.REDIS_PORT)


#定义函数，工厂函数，用来生产app，通过传入的参数的不同，可以生产不同配置环境的app
def create_app(config_name):
        from info.modules.index import index_blue  #导入蓝图
        from info.modules.passport import passport_blue   #导入实现验证码的蓝图
        from info.modules.profile import profile_blue  # 导入个人中心蓝图
        from info.modules.admin import  admin_blue  #导入后台管理员蓝图


        app=Flask(__name__)
        #使用配置对象
        app.register_blueprint(index_blue)              #注册第一个蓝图
        app.register_blueprint(passport_blue)       #注册第二个蓝图
        app.register_blueprint(profile_blue)            #注册第三个蓝图
        app.register_blueprint(admin_blue)             #注册第四个蓝图

        app.config.from_object(config_dict[config_name])
        #通过函数来让db和app进行关联
        db.init_app(app)
        #Session 初始化
        Session(app)

        # 添加过滤器实现点击排行的类名过滤
        from info.utils.commons import index_filter
        app.add_template_filter(index_filter,'index_filter')

        #开启CSRF保护功能
        CSRFProtect(app)

        #生成csrf_token,并且把token 写入到客户端的cookie中
        @app.after_request
        def after_request(reponse):
                csrf_token=csrf.generate_csrf()
                reponse.set_cookie('csrf_token',csrf_token)
                return reponse



        return app