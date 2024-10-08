from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from exts import mail, db
from flask_mail import Message
import string
import random
from .forms import RegisterForm, LoginForm
from models import UserModel
from werkzeug.security import generate_password_hash, check_password_hash
# 暂时数据库存储验证码
from models import EmailCaptchaModel
bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    form = LoginForm(request.form)
    if form.validate():
        email = form.email.data
        password = form.password.data
        user = UserModel.query.filter_by(email == email).first()
        if user and user.check_password(password):
            # cookie:存储登录授权的信息
            # flask session 加密存储在cookie中
            session['user_id'] = user.id
            return redirect("/")
        else:
            print('邮箱或密码错误')
            return redirect(url_for("auth.login"))
    else:
        print(form.errors)
        return redirect(url_for("auth.login"))

@bp.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    # 表单验证 flask-wtf:wtf-form
    form = RegisterForm(request.form)
    if form.validate():
        email = form.email.data
        username = form.username.data
        password = form.password.data
        user = UserModel(email=email, username=username, password=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("auth.login"))
    else:
        print(form.errors)
        return redirect(url_for("auth.register"))

@bp.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# TODO: 全局创建一个 email * (captcha, timestamp_at_creation) dict
# 每次这个函数（发送验证码）被调用，都把这个用户的 email 和生成的验证码
# 推到这个 dict 中。每次验证，比较：
# 1. 验证码是否正确
# 2. 验证码是否过期（用户发送的和 dict 中存储的 timestamp 差）
# 每次调用，扫遍这个 dict，删掉过期的验证码项
@bp.route("/captcha/email", methods=['GET'])
def get_email_captcha():
    email = request.args.get("email")
    source = string.digits*4
    captcha = random.sample(source, 4)
    captcha = "".join(captcha)
    message = Message(subject='注册验证码', recipients=[email], body='你的验证码是：'+captcha)
    mail.send(message)
    '''
    todo: redis
    1. 保存验证码到数据库
    2. 验证码有效时间
    '''
    # 暂时采用数据库存储
    email_captcha = EmailCaptchaModel(email=email, captcha=captcha)
    db.session.add(email_captcha)
    db.session.commit()
    # RESTful API
    # {code:200/400/500, message:"", data:{}}
    return jsonify({"code":200, "message":"", "data":None})

@bp.route("/mail/test")
def test_mail():
    message = Message(subject='邮箱测试', recipients=['@qq.com'], body='测试邮件')
    mail.send(message)
    return '邮件发送成功！'
