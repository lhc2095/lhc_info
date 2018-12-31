from flask import current_app,g, redirect, render_template, request,jsonify,session
from info import db, constants
from info.utils.response_code import RET
from . import  profile_blue
#导入登录验证装饰器
from info.utils.commons import  login_required
#导入七牛云
from info.utils.image_storage import storage
#导入模型类,新闻分类
from info.models import  Category,News


@profile_blue.route("/user_info")
@login_required
def user_info():
    user=g.user
    if not user:
        return redirect('/')
    data ={
        'user':user.to_dict()
    }
    return render_template('news/user.html', data=data)



@profile_blue.route('/base_info',methods=['GET','POST'])
@login_required
def base_info():
    user=g.user
    # get 请求加载模板
    if  request.method == 'GET':
        data={
            'user':user.to_dict()
        }
        return render_template('news/user_base_info.html',data=data)

   #post请求请求数据 ajax
    nick_name=request.json.get('nick_name')
    signature=request.json.get('signature')
    gender=request.json.get('gender')
    if not any([nick_name,signature,gender]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数缺失')
    if gender not in ['MAN','WOMEN']:
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误')
    user.nick_name=nick_name
    user.signature=signature
    user.gender=gender
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='保存用户信息失败')
    #更新redis中的缓存信息,昵称
    session['nick_name']=nick_name
    return jsonify(errno=RET.OK,errmsg='OK')

@profile_blue.route('/pic_info',methods=['GET','POST'])
@login_required
def pic_info():
    user=g.user

    if request.method =='GET':
        data={
            'user':user.to_dict()
        }
        return  render_template('news/user_pic_info.html',data=data)

    avatar= request.files.get('avatar')
    if not avatar:
        return jsonify(errno=RET.PARAMERR,errmsg='没有获取到参数')
    try:
        image_data=avatar.read()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='数据读取错误')

    #调取七牛云,获取七牛云返回的图片名称
    try:
        image_name=storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR,errmsg='上传图片异常')

    user.avatar_url=image_name
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='保存图片数据失败')
    avatar_url=constants.QINIU_DOMIN_PREFIX+image_name
    data={
        'avatar_url': avatar_url
    }
    #返回结果
    return jsonify(errno=RET.OK,errmsg='OK',data=data)


@profile_blue.route('/news_release',methods=['GET','POST'])
@login_required
def news_release():
    user=g.user
    if request.method=='GET':
        try:
            categories=Category.query.all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR,errmsg='查询新闻分类数据失败')
        if not categories:
            return jsonify(errno=RET.NODATA,errmsg='无新闻分类数据')
        category_list=[]
        for category in categories:
            category_list.append(category.to_dict())
        #移除最新分类
        category_list.pop(0)
        data={
            "categories":category_list
        }
        return render_template('news/user_news_release.html',data=data)


    #获取参数  title,category_id,digest,index_image,content
    title=request.form.get("title")
    category_id=request.form.get('category_id')
    digest=request.form.get('digest')
    content = request.form.get('content')
    index_image=request.files.get('index_image')


    if not all([title,category_id,digest,index_image,content]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数缺失')
    #转换数据类型
    try:
        category_id=int(category_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR,errmsg='参数类型错误')

    #读取图片数据
    try:
        image_name=index_image.read()
    except  Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR,errmsg='读取新闻图片错误')
    #调用七牛云上传图片
    try:
        news_image =storage(image_name)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR,errmsg='上传图片失败')

    #定义绝对图片地址
    news=News()
    news.title=title
    news.category_id=category_id
    news.digest=digest
    news.content=content
    news.index_image_url=constants.QINIU_DOMIN_PREFIX+news_image
    news.user_id=user.id
    news.status=1
    news.source="个人发布"
    try:
        db.session.add(news)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='保存数据失败')

    return jsonify(errno=RET.OK,errmsg='OK')

