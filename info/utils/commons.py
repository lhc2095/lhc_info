# 实现自定义过滤器
def index_filter(index):
    if index ==0:
            return 'first'
    elif index == 1:
            return 'second'
    elif index == 2:
            return 'third'
    else:
            return ''

#定义函数,封装检查用户是否登录功能.
from flask import session, current_app, g
from info.models import User
import functools

def  login_required(f):
        @functools.wraps(f)
        def wrapper(*args,**kwargs):
            user_id=session.get('user_id')
            user = None         #为了避免因为使用try后导致的user可能不被定义的错误
            if user_id:
                    try:
                        user=User.query.filter_by(id=user_id).first()
                    except Exception as e:
                        current_app.logger.error(e)
            g.user = user
            return f(*args,**kwargs)
        return wrapper