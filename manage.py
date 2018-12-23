# 导入管理器
from flask_script import Manager
#导入迁移框架
from flask_migrate import MigrateCommand,Migrate
#从初始化文件中导入app,添加导入的模型类文件models
from info import create_app,db,models






app=create_app('development')
#实例化管理器对象
manage=Manager(app)
#使用迁移框架
Migrate(app,db)
#添加迁移命令
manage.add_command('db',MigrateCommand)



if __name__ == '__main__':
    manage.run()