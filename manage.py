# 导入管理器
from flask import current_app
from flask_script import Manager
#导入迁移框架
from flask_migrate import MigrateCommand,Migrate
#从初始化文件中导入app,添加导入的模型类文件models
from info import create_app,db,models
#添加模型类
from info.models import User

app=create_app('development')
#实例化管理器对象
manage=Manager(app)
#使用迁移框架
Migrate(app,db)
#添加迁移命令
manage.add_command('db',MigrateCommand)



@manage.option('-n','-name',dest='name')
@manage.option('-p','-password',dest='password')
def create_supperuser(name,password):
    if not all([name,password]):
        print('参数缺失')
    user = User()
    user.mobile=name
    user.nick_name=name
    user.password=password
    user.is_admin=True
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(e)
    print('创建管理员用户成功')



if __name__ == '__main__':
    print(app.url_map)
    manage.run()