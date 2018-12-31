from . import  index_blue
from flask import session, render_template, current_app, request, jsonify, g
from info.models import User, Comment,CommentLike
from info.models import Category,News
from info.utils.response_code import RET
from info.utils.commons import login_required
from info import constants, db
# 导入自定的登录验证装饰器
from info.utils.commons import  login_required
from datetime import datetime


@index_blue.route('/')
@login_required
def index():

    user=g.user

#新闻分类 ------------------------------------------------------------------------------------
    try:
        categories =Category.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="查询数据失败")

    if not categories:
        return jsonify(errno=RET.NODATA,errmsg='无新闻分类数据')

    category_list=[]
    for category in categories:
        category_list.append(category.to_dict())

#新闻点击排行 ------------------------------------------------------------------------------------

    try:
        news_list=News.query.order_by(News.clicks.desc()).limit(6)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询新闻点击排行失败')
    #判断查询结果
    if not news_list:
        return jsonify(errno=RET.NODATA,errmsg='无新闻排行数据')
    #遍历查询结果
    new_list=[]
    for new in news_list:
        new_list.append(new.to_dict())

    data ={
            'user_info':user.to_dict()   if user else None,
            'category_list':category_list,
            'new_list':new_list
        }
    return render_template ('news/index.html',data=data)

#新闻列表 ------------------------------------------------------------------------------------
@index_blue.route('/news_list')
def get_news_list():
    """
    1.获取参数,cid(新闻分类id),total_page(总页数),per_page(每页的数据个数)
    2.检查参数
    3.从数据库中取出来,
    :return:
    """
    cid=request.args.get('cid','1')                               #  前端 index.js 文件里是利用  get版的ajax 来传递参数的  ,没有指定contentType,所以使用args获取参数
    page=request.args.get('page','1')
    per_page=request.args.get('per_page','10')

    try:
        cid,page,per_page=int(cid),int(page),int(per_page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR,errmsg='参数类型错误')
    filters=[]

    if cid>1:
        filters.append(News.category_id==cid)
    try:
        paginate= News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page,per_page,False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询数据错误')
    current_page=paginate.page
    news_list=paginate.items
    total_page=paginate.pages
    new_list=[]
    for new in news_list:
        new_list.append(new.to_dict())
    data={
        'current_page':current_page,
        'new_list':new_list,
        'total_page':total_page
    }
    return jsonify(errno=RET.OK,errmsg='OK',data=data)

#新闻详情  ------------------------------------------------------------------------------------
@index_blue.route('/<int:news_id>')
@login_required
def get_news_detail(news_id):

    # 右上角用户状态         ----------
    # user_id = session.get('user_id')
    # user = None  # 为了避免因为使用try后导致的user可能不被定义的错误
    # if user_id:
    #     try:
    #         user = User.query.filter_by(id=user_id).first()
    #     except Exception as e:
    #         current_app.logger.error(e)
    user=g.user

    # 点击排行          ---------
    try:
        news_list=News.query.order_by(News.clicks.desc()).limit(6)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询新闻点击排行失败')
    #判断查询结果
    if not news_list:
        return jsonify(errno=RET.NODATA,errmsg='无新闻排行数据')
    #遍历查询结果
    new_list=[]
    for new in news_list:
        new_list.append(new.to_dict())

# 新闻详情数据    ---------------------------
    try:
        news=News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询数据失败')
    if not news:
        return jsonify(errno=RET.NODATA,errmsg='无新闻详情数据')

    news.clicks+=1
    try:
        db.session.add(news)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='数据保存失败')
    is_collected= False
    if user and news in user.collection_news:
        is_collected=True

    # 展示新闻评论信息
    try:
        comments=Comment.query.filter(Comment.news_id == news_id).order_by(Comment.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询新闻评论信息失败')
    comments_list=[]
    for comment in comments:
        comments_list.append(comment.to_dict())
    data ={
            'user_info':user.to_dict()   if user else None,
            'new_list':new_list,
            'new_detail':news.to_dict(),                          # news.to_dict() 将新闻对象返还给前端，前端根据标签格式拿出内容放在前端的标签格式中
            'comments':comments_list
        }
    return render_template ('news/detail.html',data=data)


# 新闻收藏          ----------------------------------------
@index_blue.route("/news_collect",methods=['POST'])
@login_required
def user_collection():
    user=g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR,errmsg='用户未登陆')

    #获取参数
    news_id= request.json.get('news_id')
    action=request.json.get('action')
    #检查参数完整性
    if not all([news_id,action]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数缺失')

    try:
        news_id=int(news_id)                 # 数据类型转换,方便mysql数据查询
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR,errmsg='参数类型错误')
    if action not in ['collect','cancel_collect']:
        return jsonify(errno=RET.PARAMERR,errmsg='参数范围错误')

    try:
        news = News.query.get(news_id)           # 获取用户当前浏览的新闻
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询新闻数据失败')
    if not news:
        return jsonify(errno=RET.NODATA,errmsg='没有新闻数据')

    if action == 'collect':
        if news not in user.collection_news:
            user.collection_news.append(news)      # 添加新闻到用户收藏中
    else:
            user.collection_news.remove(news)

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DATAERR,errmsg='数据保存失败')
    return jsonify(errno=RET.OK,errmsg='OK')





# 新闻评论 -----------------------------------------------
@index_blue.route('/news_comment',methods=['POST'])
@login_required
def news_commend():
    user=g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR,errmsg='用户未登录')
    new_id=request.json.get('new_id')
    # print(new_id)
    content=request.json.get('content')
    parent_id=request.json.get('parent_id')
    if not all([new_id,content]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数不完整')
    try:
        new_id=int(new_id)
        if parent_id:
            parent_id=int(parent_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR,errmsg=' 参数类型错误')
    try :
        news =News.query.get(new_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询数据失败')
    if not news:
        return jsonify(errno=RET.NODATA,errmsg='没有新闻数据')
    # 构造模型类对象
    comment=Comment()
    comment.news_id = news.id            #评论的新闻的id
    comment.content=content               #评论的内容
    comment.user_id=user.id                 # 登陆的用户评论的,记录登录用户id
    #如果存在父评论 ----------------
    if parent_id:
        comment.parent_id =parent_id
    try:
        db.session.add(comment)
        db.session.commit()
    except Exception  as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='保存评论信息失败')
    return jsonify(errno=RET.OK,errmsg='OK',data=comment.to_dict())

# 评论点赞 --------------------------------------------------
@index_blue.route('/comment_like',methods=['POST'])
@login_required
def comment_up():
    user=g.user
    commentid=request.json.get("comment_id")
    newsid=request.json.get('news_id')

    try:
        commentid=int(commentid)
        newsid=int(newsid)
    except Exception as e:
        return jsonify(errno=RET.PARAMERR,errmsg='数据类型错误')
    if not all([commentid,newsid]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数缺失')

    try:
        comment_like = CommentLike.query.filter(CommentLike.comment_id == commentid,CommentLike.user_id==user.id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据库失败')

    try:
        comment=Comment.query.get(commentid)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询数据库失败')


    if not comment_like:
        comment_like=CommentLike()
        comment.like_count+=1
        comment_like.comment_id=commentid
        comment_like.user_id=user.id
        comment_like.update_time=datetime.now()
        comment_like.create_time=comment.create_time
        num = comment.like_count
        try:
            db.session.add(comment_like)
            db.session.add(comment)
            db.session.commit()
        except  Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify(errno=RET.DBERR,errmsg='数据库保存失败')
        return jsonify(errno=RET.OK,errmsg='OK',num=num)
    else:
        db.session.delete(comment_like)
        comment.like_count-=1
        num=comment.like_count
        try:
            db.session.commit()
        except  Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify(errno=RET.DBERR,errmsg='数据库保存失败')
        return jsonify(errno=RET.OK,errmsg='OK',num=num)









@index_blue.route('/favicon.ico')            # 浏览器上方的小logo,浏览器每次都会默认调用/favicon.ico
def favicon():
    return current_app.send_static_file('news/favicon.ico')