from flask import Blueprint, session, request,redirect,url_for

admin_blue=Blueprint('admin_blue',__name__,url_prefix='/admin')

from . import views

#权限检验,作用:让普通用户无法访问到后台页面
# @admin_blue.before_request
# def check_admin():
#     is_admin=session.get('is_admin',False)
#
#     if not is_admin and not request.url.endswith(url_for('admin_blue.login')):
#         return redirect('/')