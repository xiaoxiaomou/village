from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))  # 增加长度以适应新的哈希值
    role = db.Column(db.String(20), default='user')
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    messages = db.relationship('Message', backref='user', lazy=True)
    replies = db.relationship('Reply', backref='admin', lazy=True)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    news = db.relationship('News', backref='category', lazy=True)

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    author = db.Column(db.String(80))
    image_url = db.Column(db.String(255))

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    file_url = db.Column(db.String(255))

class Government(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text)
    file_url = db.Column(db.String(255))
    create_time = db.Column(db.DateTime, default=datetime.utcnow)

class VillageInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(255))

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    contact = db.Column(db.String(100))
    content = db.Column(db.Text, nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    reply = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    replies = db.relationship('Reply', backref='message', lazy=True)

class Reply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    message_id = db.Column(db.Integer, db.ForeignKey('message.id'))
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class VillageLogo(db.Model):
    """乡村Logo模型"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # 乡村名称
    logo_url = db.Column(db.String(255), nullable=False)  # Logo图片URL
    description = db.Column(db.Text)  # Logo描述
    is_active = db.Column(db.Boolean, default=True)  # 是否启用
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class VillageCarousel(db.Model):
    """乡村风光轮播图模型"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)  # 图片标题
    image_url = db.Column(db.String(255), nullable=False)  # 图片URL
    description = db.Column(db.Text)  # 图片描述
    link_url = db.Column(db.String(255))  # 点击跳转链接
    sort_order = db.Column(db.Integer, default=0)  # 排序顺序
    is_active = db.Column(db.Boolean, default=True)  # 是否启用
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)