from . import  passport_blue
from flask import request,jsonify,current_app,make_response,session
from info.utils.captcha.captcha import captcha
from info.utils.response_code  import RET
from info import  redis_store,constants,db
from info.models import User
from libs.yuntongxun import sms
from datetime import  datetime
import re,random




@passport_blue.route('/image_code')
def generate_image_code():
        """
        1.前端文件在点击注册后便调用此函数，用来生成一个图形验证码
        2.生成图形验证码调用了 utiles.captcha.cpatcha.cpatcha,然后会返回一个图片，文本，名字
        3.接收到前端传来的uuid，用来标识随机验证码
        3.将传来的文本验证码存储到redis当中，通过键值对（uuid:文本验证码），数据库操作要用try
        4.存储成功后，要通过make_response 来制造一个响应对象，将验证码图片传输进去
        5.返回相应对象

        """

        image_code_id=request.args.get("image_code_id")
        if not image_code_id:
            return jsonify(errno=RET.PARAMERR,errmsg='参数错误')

        name,text,image = captcha.generate_captcha()
        # print('进来了')
        # 在redis中存储验证码的text内容
        try:
            redis_store.setex('ImageCode_'+image_code_id,constants.IMAGE_CODE_REDIS_EXPIRES,text)
        except Exception as e:
            #记录错误信息到日志文件中
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR,errmsg='保存数据失败')
        else:
            response=make_response(image)  #生成一个响应的对象，第一个参数是相应的正文，即响应主体
            response.headers['Content-Type']='image/jpg'
            return response

@passport_blue.route('/sms_code',methods=['POST'])
def send_sms_code():    #发送短信
            """
            1.前端点击发送手机验证码的时候会调用该函数
            2.main.js文件中调用ajxs传过来json数据
            3.定义变量获取这三个数据参数，分别是mobile(手机),image_code(用户输入的图形验证码),image_code_id(UUID)
            4.检查参数完整性，all([mobile,image_code,image_code_id]), all()里面可以传入可迭代对象
            5.检查参数正确性：（对redis进行操作时要使用try.....except）
                  一.图片验证码
                    ①根据键名("Image_Code"+image_code_id)从redis中拿出存储的真实图形验证码的字符串
                    ②用保存了用户输入的验证码的变量 image_code 与 上一步中拿出的 真实图形验证码 的值进行 判断对比（注意两个变量同时lower()或者upper(),来忽略大小写）
                    ③为了防范机器恶意对比验证码，所以图形验证码只能使用一次，判断对比完删除
                  二.手机验证码
                    ① 利用正则表达式判断手机号码格式  re.match('1[3456789]/d{9}$')
                    ②判断手机号是否已经注册，从mysql中根据手机号查找，如过有，return 已经注册
                    ③生成随机6位短信验证码    sms_code= '%06d'%random.randint(0,999999)
                    ④将验证码以键为（''SMSCode_'+mobile'），值为 smc_code ，来存进redis中
            6.发送手机验证码（利用云通讯）:
                    ccp=sms.CCP()                 # 创建类对象
                    result=ccp.send_template_sms(mobile,[sms_code,constants.SMS_CODE_REDIS_EXPIRES/60],1)              #调用类方法返回给参数result为0即成功，第一个参数：手机号；第二个参数：手机验证码；第三个参数：过期时间（分钟）；第四个参数：模板，默认为1

            """
            mobile=request.json.get('mobile')
            image_code=request.json.get('image_code')
            image_code_id=request.json.get('image_code_id')
            if not all([mobile,image_code,image_code_id]):
                return jsonify(errno=RET.PARAMERR,errmsg='参数缺失')
            # 正则检查手机号是否格式正确
            if not re.match(r'1[3456789]\d{9}$',mobile):
                return jsonify(errno=RET.PARAMERR,errmsg='手机格式错误')
            try:
                real_image_code=redis_store.get('ImageCode_'+image_code_id)
            except Exception as e:
                current_app.logger.error(e)
                return jsonify(errno=RET.DBERR,errmsg='获取数据失败')
            if not real_image_code:
                return jsonify(erron=RET.NODATA,errmsg='数据已失效')
            # 图形验证码只能比较一次，所以删除redis里存储的验证码
            try:
                redis_store.delete('ImageCode_'+image_code_id)
            except Exception as e:
                current_app.logger.error(e)
            real_image_code=bytes.decode(real_image_code)
            if real_image_code.lower() != image_code.lower():
                print(real_image_code.lower())
                print(image_code.lower())
                return jsonify(error=RET.DATAERR,errmsg='图片验证码错误')
            #检查用户是否注册
            try:
                user=User.query.filter_by(mobile=mobile).first()
            except Exception as e:
                current_app.logger.error(e)
                return jsonify(errno=RET.DBERR,errmsg='查询数据失败')
            else:
                if  user:
                    return jsonify(errno=RET.DATAEXIST,errmsg='手机号已经注册')

            sms_code='%06d'% random.randint(0,999999)
            print(sms_code)
            try:
                redis_store.setex('SMSCode_'+mobile,constants.SMS_CODE_REDIS_EXPIRES,sms_code)
            except Exception as e:
                current_app.logger.error(e)
                return jsonify(errno=RET.DBERR,errmsg='保存数据失败')
            #使用云通讯发送短信
            try:
                ccp = sms.CCP()                                                                                                                                                            # 创建类对象
                result = ccp.send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES / 60],1)  # 调用类方法返回给参数result为0即成功，第一个参数：手机号；第二个参数：手机验证码；第三个参数：过期时间（分钟）；第四个参数：模板，默认为1

            except Exception as e:
                current_app.logger.error(e)
                return jsonify(errno=RET.THIRDERR,errmsg='发送短信异常')
            if result == 0:
                return  jsonify(errno=RET.OK,errmsg='发送成功')
            else:
                return jsonify(errno=RET.THIRDERR,errmsg='发送失败')


@passport_blue.route('/register',methods=['POST'])
def register():
    """
    1.获取前端发来的参数mobile,sms_code,password
    2.检查参数是否完整
    3.检查参数的正确性
        ①检查手机号格式
        ②检查手机号是否未被注册
        ③判断验证码是否已经过期
        ④从redis中拿出验证码与用户输入的验证码进行对比

    :return:
    """
    mobile=request.json.get('mobile')
    sms_code=request.json.get('sms_code')
    password=request.json.get('password')
    if not all([mobile,sms_code,password]):
        return jsonify(errno=RET.PARAMERR,errmsg='输入的参数不全')
    if not re.match(r'1[3456789]\d{9}$',mobile):
        return jsonify(errno=RET.PARAMERR,errmsg='手机格式错误')
    try:
        real_sms_code=redis_store.get('SMSCode_'+mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='获取数据错误')

    if not real_sms_code:
        return jsonify(errno=RET.NODATA,errmsg='验证码已经过期')
    real_sms_code=bytes.decode(real_sms_code)

    if real_sms_code != sms_code:
        return jsonify(errno=RET.DATAERR,errmsg='输入的手机验证码有误')

    try:
        user=User.query.filter(User.mobile==mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询用户数据失败')
    else:
        if user:
            return jsonify(errno=RET.DATAEXIST,errmsg='用户已经注册')

    user=User()
    user.mobile=mobile
    user.nick_name=mobile
    user.password=password

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DATAERR,errmsg='保存数据失败')

    session['user_id']=user.id
    session['mobile']=mobile
    session['nick_name']=mobile

    return  jsonify(errno=RET.OK,errmsg='创建用户成功')

@passport_blue.route('/login',methods=["POST"])
def login():
    """
    1.获取前端发送过来的用户名,密码
    2.从mysql数据库中比对用户名和密码,错误返回错误信息
    3.比对成功后,改变html页面的右上角状态
    :return:
    """
    mobile=request.json.get("mobile")
    password=request.json.get("password")

    if not all([mobile,password]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数缺失')
    if not re.match(r'1[3456789]\d{9}$'):
        return jsonify(errno=RET.PARAMERR,errmsg='手机号码格式错误')
    try:
        user=User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询数据失败')

    if not user or not user.check_password(password):
        return jsonify(errno=RET.PWDERR,errmsg='用户名或密码错误')
    user.last_login=datetime.now()

    try:
        db.session.add(user)       # 提交的登录时间
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()           # 回滚到最近的commit前
        return jsonify(errno=RET.DBERR,errmsg='保存用户数据失败')

    session['user_id']=user.id
    session['mobile']=mobile
    session['nick_name']=user.nick_name

    return jsonify(errno=RET.OK,errmsg='OK')






