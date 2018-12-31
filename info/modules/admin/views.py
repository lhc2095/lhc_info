from . import admin_blue
from flask import render_template, request, g, session, redirect, url_for, current_app,jsonify
from info.utils.commons import login_required
from info.models import User
from info import constants
from info.utils.response_code import RET


# 后台管理页面 ---------------------------------------------------------------------
@admin_blue.route('/index')
@login_required
def index():

    nick_name=session.get('nick_name')
    user_id=session.get('user_id')
    data={
        "nick_name":nick_name,
        'user_id':user_id
    }
    user=User.query.filter(User.id==user_id).first()
    return render_template('admin/index.html',data=data,user=user.to_dict())


# 管理员登录页面 -------------------------------------------------------------
@admin_blue.route('/login')
def login():

    if request.method=='GET':
        user_id=session.get('user_id',None)
        isadmin=session.get('isadmin',None)
        if isadmin and user_id:
            return redirect(url_for('admin_blue.index'))
    return render_template('admin/login.html')

@admin_blue.route('/login_in',methods=['GET','POST'])
def login_in():
    #获取参数
    user_name=request.json.get('username')
    password=request.json.get('password')

    if not all([user_name,password]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数不完整')

    try:
        user=User.query.filter(User.mobile==user_name,User.is_admin==True).first()
    except Exception as e:
        current_app.logger.error(e)
        return  jsonify(errno=RET.DBERR,errmsg='查询错误')
    if user is None or not user.check_password:
        return jsonify(errno=RET.NODATA, errmsg='没有此用户')
    session['user_id']=user.id
    session['mobile']=user.mobile
    session['nick_name']=user.nick_name
    session['is_admin']=user.is_admin
    return jsonify(errno=RET.OK,errmsg='OK')


# 用户统计页面 --------------------------------------------------------------
@admin_blue.route('/user_count')
@login_required
def user_count():
    return render_template('admin/user_count.html')



