"""
记忆数据库模型
全部使用SQLite兼容语法
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    role = db.Column(db.String(20), default="user")
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    messages = db.relationship("Message", backref="user", lazy=True)
    replies = db.relationship("Reply", backref="admin", foreign_keys="Reply.admin_id", lazy=True)
    memories = db.relationship("Memory", backref="author", lazy=True)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    news = db.relationship("News", backref="category", lazy=True)


class News(db.Model):
    __tablename__ = "news"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    author = db.Column(db.String(80))
    image_url = db.Column(db.String(255))
    view_count = db.Column(db.Integer, default=0)  # 浏览次数


class Service(db.Model):
    __tablename__ = "services"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    file_url = db.Column(db.String(255))


class Government(db.Model):
    __tablename__ = "government"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text)
    file_url = db.Column(db.String(255))
    create_time = db.Column(db.DateTime, default=datetime.utcnow)


class VillageInfo(db.Model):
    __tablename__ = "village_info"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    image_url = db.Column(db.String(255))


class Message(db.Model):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    contact = db.Column(db.String(100))
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    reply = db.Column(db.Text)
    replies = db.relationship("Reply", backref="message", lazy=True)


class Reply(db.Model):
    __tablename__ = "replies"
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    message_id = db.Column(db.Integer, db.ForeignKey("messages.id"))
    admin_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class VillageLogo(db.Model):
    __tablename__ = "village_logo"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    logo_url = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class VillageCarousel(db.Model):
    __tablename__ = "village_carousel"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    link_url = db.Column(db.String(255))
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Memory(db.Model):
    """多媒体记忆记录 - 核心模型"""
    __tablename__ = "memories"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    content = db.Column(db.Text)
    reflection = db.Column(db.Text)
    memory_type = db.Column(db.String(20), default="text")
    date_recorded = db.Column(db.Date, default=lambda: datetime.utcnow().date())
    photo_urls = db.Column(db.Text, default="[]")
    video_urls = db.Column(db.Text, default="[]")
    audio_url = db.Column(db.String(500))
    audio_duration = db.Column(db.String(50))
    thumbnail = db.Column(db.String(500))
    people_involved = db.Column(db.Text, default="[]")
    locations = db.Column(db.Text, default="[]")
    tags = db.Column(db.Text, default="[]")
    is_public = db.Column(db.Boolean, default=True)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    def get_photos(self):
        try: return json.loads(self.photo_urls) or []
        except: return []
    def get_videos(self):
        try: return json.loads(self.video_urls) or []
        except: return []
    def get_tags(self):
        try: return json.loads(self.tags) or []
        except: return []
    def get_people(self):
        try: return json.loads(self.people_involved) or []
        except: return []
    def get_locations(self):
        try: return json.loads(self.locations) or []
        except: return []


class Tag(db.Model):
    """标签分类"""
    __tablename__ = "tags"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    category = db.Column(db.String(20), default="general")
    color = db.Column(db.String(7), default="#4a90d9")
    memory_count = db.Column(db.Integer, default=0)


class MemoryTag(db.Model):
    """记忆-标签关联"""
    __tablename__ = "memory_tags"
    memory_id = db.Column(db.Integer, db.ForeignKey("memories.id"), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey("tags.id"), primary_key=True)
    tag_category = db.Column(db.String(20))


class People(db.Model):
    """人物档案"""
    __tablename__ = "people"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    relation = db.Column(db.String(100))
    photo_url = db.Column(db.String(500))
    bio = db.Column(db.Text)
    birth_year = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Backup(db.Model):
    """数据备份"""
    __tablename__ = "backups"
    id = db.Column(db.Integer, primary_key=True)
    backup_type = db.Column(db.String(20), default="full")
    storage_path = db.Column(db.String(500))
    file_size = db.Column(db.Integer, default=0)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="completed")


class PendingUser(db.Model):
    """待审核用户注册申请"""
    __tablename__ = "pending_users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    nickname = db.Column(db.String(50))
    password_hash = db.Column(db.String(255), nullable=False)
    avatar_url = db.Column(db.String(500), default='')
    bio = db.Column(db.Text, default='')
    status = db.Column(db.String(20), default="pending")  # pending, approved, rejected
    admin_note = db.Column(db.Text, default='')  # 管理员备注
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    reviewed_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    review_comment = db.Column(db.Text, default='')  # 审核意见

    reviewer = db.relationship("User", foreign_keys=[reviewed_by], backref="reviews")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class MediaFile(db.Model):
    """用户上传的媒体文件"""
    __tablename__ = "media_files"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), default='')
    file_type = db.Column(db.String(10), nullable=False)  # image or video
    file_url = db.Column(db.String(500), nullable=False)
    thumbnail_url = db.Column(db.String(500), default='')
    file_size = db.Column(db.Integer, default=0)  # bytes
    original_name = db.Column(db.String(255), default='')
    description = db.Column(db.Text, default='')
    is_public = db.Column(db.Boolean, default=True)
    view_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = db.relationship("User", backref="media_files")


class Notification(db.Model):
    """系统通知"""
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), default="info")  # info, success, warning, error
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    target_user = db.relationship("User", foreign_keys=[user_id], backref="notifications")


class AuditLog(db.Model):
    """操作审计日志"""
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    operator_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    action = db.Column(db.String(50), nullable=False)  # register, approve, reject, upload
    target_type = db.Column(db.String(50), default='')  # user, media
    target_id = db.Column(db.Integer, default=0)
    detail = db.Column(db.Text, default='')
    ip_address = db.Column(db.String(45), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    operator = db.relationship("User", foreign_keys=[operator_id], backref="audit_logs")
