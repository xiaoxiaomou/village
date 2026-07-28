"""
记忆数据库模型
全部使用SQLite兼容语法
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()


def _json_list(text):
    """将 JSON 文本解析为列表；解析失败或类型不符时返回空列表。

    仅捕获 ``json.JSONDecodeError`` / ``TypeError``，避免吞掉其它异常。
    """
    try:
        result = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return []
    return result if isinstance(result, list) else []


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    role = db.Column(db.String(20), default="user")
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    messages = db.relationship("Message", backref="user", lazy=True)
    replies = db.relationship(
        "Reply", backref="admin", foreign_keys="Reply.admin_id", lazy=True
    )
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
    update_time = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


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
    update_time = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


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
    update_time = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def get_photos(self):
        return _json_list(self.photo_urls)

    def get_videos(self):
        return _json_list(self.video_urls)

    def get_tags(self):
        return _json_list(self.tags)

    def get_people(self):
        return _json_list(self.people_involved)

    def get_locations(self):
        return _json_list(self.locations)


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
    avatar_url = db.Column(db.String(500), default="")
    bio = db.Column(db.Text, default="")
    status = db.Column(db.String(20), default="pending")  # pending, approved, rejected
    admin_note = db.Column(db.Text, default="")  # 管理员备注
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    reviewed_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    review_comment = db.Column(db.Text, default="")  # 审核意见

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
    title = db.Column(db.String(200), default="")
    file_type = db.Column(db.String(10), nullable=False)  # image or video
    file_url = db.Column(db.String(500), nullable=False)
    thumbnail_url = db.Column(db.String(500), default="")
    file_size = db.Column(db.Integer, default=0)  # bytes
    original_name = db.Column(db.String(255), default="")
    description = db.Column(db.Text, default="")
    is_public = db.Column(db.Boolean, default=True)
    view_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    owner = db.relationship("User", backref="media_files")


class Notification(db.Model):
    """系统通知"""

    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    notification_type = db.Column(
        db.String(50), default="info"
    )  # info, success, warning, error
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    target_user = db.relationship(
        "User", foreign_keys=[user_id], backref="notifications"
    )


class AuditLog(db.Model):
    """操作审计日志"""

    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    operator_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    action = db.Column(
        db.String(50), nullable=False
    )  # register, approve, reject, upload
    target_type = db.Column(db.String(50), default="")  # user, media
    target_id = db.Column(db.Integer, default=0)
    detail = db.Column(db.Text, default="")
    ip_address = db.Column(db.String(45), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    operator = db.relationship("User", foreign_keys=[operator_id], backref="audit_logs")


class SiteContact(db.Model):
    """网站联系信息（单行配置，由后台维护）"""

    __tablename__ = "site_contact"
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(200), default="")  # 村委会地址
    phone = db.Column(db.String(50), default="")  # 联系电话
    mobile = db.Column(db.String(50), default="")  # 手机号码
    email = db.Column(db.String(120), default="")  # 电子邮箱
    website = db.Column(db.String(200), default="")  # 官方网站
    work_hours = db.Column(db.Text, default="")  # 办公时间（多行文本）
    work_note = db.Column(db.Text, default="")  # 特别提醒说明（多行文本）
    public_transit = db.Column(db.Text, default="")  # 公共交通（多行文本）
    driving_route = db.Column(db.Text, default="")  # 自驾路线（多行文本）
    wechat = db.Column(db.String(100), default="")  # 微信号
    map_embed = db.Column(db.Text, default="")  # 地图嵌入代码/链接
    route_link = db.Column(db.Text, default="")  # 路线规划链接（高德/百度导航URL等）
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class HomeFeature(db.Model):
    """首页特色服务卡片（可由后台维护排序与显隐）"""

    __tablename__ = "home_features"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)  # 标题，如「生态农业」
    description = db.Column(db.Text, default="")  # 描述
    icon = db.Column(db.String(50), default="fa-leaf")  # FontAwesome 图标类名
    icon_color = db.Column(
        db.String(20), default="red"
    )  # red/jade/gold/ink 对应现有配色
    link = db.Column(db.String(200), default="/services")  # 了解更多链接
    sort_order = db.Column(db.Integer, default=0)  # 排序（越小越靠前）
    is_active = db.Column(db.Boolean, default=True)  # 是否在前台展示
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SiteConfig(db.Model):
    """站点级全局配置（单行表，id 固定 = 1）。

    站点标题、Logo、导航菜单、页脚、快速入口、首页统计等均来自此表，
    通过 ``SiteConfig.get()`` 单例获取；表为空/缺失时返回内存默认实例，
    保证模板渲染不崩溃。
    """

    __tablename__ = "site_config"
    id = db.Column(db.Integer, primary_key=True)
    site_title = db.Column(db.String(100), default="乡村记忆")  # 站点标题
    site_slogan = db.Column(db.Text, default="")  # 站点副标题/标语
    logo_url = db.Column(db.String(255), default="")  # 图片 Logo 访问 URL
    logo_name = db.Column(db.String(100), default="乡村记忆")  # 文字 Logo 名称
    logo_icon = db.Column(db.String(50), default="fas fa-mountain")  # 文字 Logo 图标
    nav_menu = db.Column(db.Text, default="[]")  # 导航菜单 JSON
    footer_brand = db.Column(db.Text, default="")  # 页脚品牌名
    footer_about = db.Column(db.Text, default="")  # 页脚简介文案
    footer_links = db.Column(db.Text, default="[]")  # 页脚链接分组 JSON
    footer_copyright = db.Column(db.Text, default="")  # 版权后缀（不含年份）
    quick_links = db.Column(db.Text, default="[]")  # 首页快速入口 JSON
    home_stats = db.Column(db.Text, default="{}")  # 首页/村情统计 JSON
    about_content = db.Column(db.Text, default="")  # 关于我们页正文（富文本）
    # ─── 村情页面可见文本（/village 后台可配，T1） ───
    hero_subtitle = db.Column(
        db.Text, default="生态宜居 · 产业兴旺 · 乡风文明"
    )  # 封面副标题
    hero_title = db.Column(db.Text, default="美丽乡村")  # 封面主标题（Hero 悬浮文字，后台可配）
    stat_labels = db.Column(db.Text, default="{}")  # KPI 标签 JSON: {population,area,output,satisfaction}
    intro_title = db.Column(db.Text, default="关于我们的村庄")  # 「关于我们的村庄」区块标题
    intro_subtitle = db.Column(db.Text, default="山水田园间，品味乡村魅力")  # 「关于我们的村庄」副文案
    features_title = db.Column(db.Text, default="乡村特色")  # 「乡村特色」区块标题
    features_subtitle = db.Column(db.Text, default="生态、生产、生活融合发展")  # 「乡村特色」副文案
    village_info_title = db.Column(db.Text, default="村庄信息")  # 「村庄信息」区块标题（P1）
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    @classmethod
    def default_values(cls):
        """返回默认配置字典（用于种子初始化与兜底实例）。"""
        nav_menu = [
            {"label": "首页", "url": "/", "icon": "fas fa-home", "sort_order": 1, "is_active": True},
            {"label": "新闻", "url": "/news", "icon": "fas fa-newspaper", "sort_order": 2, "is_active": True},
            {"label": "村情", "url": "/village", "icon": "fas fa-map-marked-alt", "sort_order": 3, "is_active": True},
            {"label": "政务", "url": "/government", "icon": "fas fa-landmark", "sort_order": 4, "is_active": True},
            {"label": "服务", "url": "/services", "icon": "fas fa-concierge-bell", "sort_order": 5, "is_active": True},
            {"label": "留言", "url": "/message", "icon": "fas fa-comments", "sort_order": 6, "is_active": True},
            {"label": "联系", "url": "/contact", "icon": "fas fa-phone-alt", "sort_order": 7, "is_active": True},
            {"label": "时间轴", "url": "/timeline", "icon": "fas fa-clock", "sort_order": 8, "is_active": True},
            {"label": "怀旧", "url": "/memories", "icon": "fas fa-images", "sort_order": 9, "is_active": True},
        ]
        footer_links = [
            {
                "title": "快速导航",
                "links": [
                    {"label": "新闻动态", "url": "/news"},
                    {"label": "村情概况", "url": "/village"},
                    {"label": "政务公开", "url": "/government"},
                    {"label": "便民服务", "url": "/services"},
                ],
            },
            {
                "title": "记忆空间",
                "links": [
                    {"label": "时间轴", "url": "/timeline"},
                    {"label": "怀旧记录", "url": "/memories"},
                    {"label": "留言互动", "url": "/message"},
                ],
            },
            {
                "title": "关于我们",
                "links": [
                    {"label": "联系我们", "url": "/contact"},
                    {"label": "用户登录", "url": "/login"},
                    {"label": "注册账户", "url": "/register"},
                ],
            },
        ]
        quick_links = [
            {"label": "新闻动态", "url": "/news", "icon": "fas fa-newspaper", "color": "red", "sort_order": 1},
            {"label": "村情概况", "url": "/village", "icon": "fas fa-map-marked-alt", "color": "jade", "sort_order": 2},
            {"label": "政务公开", "url": "/government", "icon": "fas fa-landmark", "color": "gold", "sort_order": 3},
            {"label": "便民服务", "url": "/services", "icon": "fas fa-concierge-bell", "color": "ink", "sort_order": 4},
            {"label": "留言互动", "url": "/message", "icon": "fas fa-comments", "color": "red", "sort_order": 5},
        ]
        home_stats = {
            "population": "2500+",
            "area": "15km²",
            "output": "1200万",
            "satisfaction": "98%",
        }
        stat_labels = {
            "population": "常住人口",
            "area": "村庄面积",
            "output": "年农业产值",
            "satisfaction": "村民满意度",
        }
        return {
            "site_title": "乡村记忆",
            "site_slogan": "",
            "logo_url": "",
            "logo_name": "乡村记忆",
            "logo_icon": "fas fa-mountain",
            "nav_menu": json.dumps(nav_menu, ensure_ascii=False),
            "footer_brand": "乡村记忆",
            "footer_about": "记录乡村的点滴变化，传承乡土文化记忆。",
            "footer_links": json.dumps(footer_links, ensure_ascii=False),
            "footer_copyright": "用心的记录，留住温暖的回忆",
            "quick_links": json.dumps(quick_links, ensure_ascii=False),
            "home_stats": json.dumps(home_stats, ensure_ascii=False),
            "about_content": (
                "<p>乡村记忆系统致力于记录乡村的点滴变化，传承乡土文化记忆。"
                "这里收藏着村庄的故事、人物与风景，让每一份乡愁都有处安放。</p>"
            ),
            # ─── 以下为本次新增（村情页面可见文本，T1） ───
            "hero_title": "美丽乡村",
            "hero_subtitle": "生态宜居 · 产业兴旺 · 乡风文明",
            "stat_labels": json.dumps(stat_labels, ensure_ascii=False),
            "intro_title": "关于我们的村庄",
            "intro_subtitle": "山水田园间，品味乡村魅力",
            "features_title": "乡村特色",
            "features_subtitle": "生态、生产、生活融合发展",
            "village_info_title": "村庄信息",
        }

    @classmethod
    def get(cls):
        """返回 id=1 的配置行；若无（表缺失/未初始化）返回内存默认实例。"""
        try:
            row = cls.query.first()
        except Exception:
            row = None
        if row is None:
            row = cls(id=1, **cls.default_values())
        return row

    @property
    def nav_items(self):
        """解析导航菜单，过滤禁用项并按 sort_order 排序。"""
        try:
            items = json.loads(self.nav_menu) if self.nav_menu else []
        except (json.JSONDecodeError, TypeError):
            items = []
        if not isinstance(items, list):
            items = []
        items = [i for i in items if i.get("is_active", True)]
        items.sort(key=lambda x: x.get("sort_order", 0))
        return items

    @property
    def footer_link_groups(self):
        """解析页脚链接分组。"""
        try:
            groups = json.loads(self.footer_links) if self.footer_links else []
        except (json.JSONDecodeError, TypeError):
            groups = []
        return groups if isinstance(groups, list) else []

    @property
    def quick_link_items(self):
        """解析首页快速入口，按 sort_order 排序。"""
        try:
            items = json.loads(self.quick_links) if self.quick_links else []
        except (json.JSONDecodeError, TypeError):
            items = []
        if not isinstance(items, list):
            items = []
        items.sort(key=lambda x: x.get("sort_order", 0))
        return items

    @property
    def home_stats_dict(self):
        """解析首页/村情统计，缺失键用兜底值补全。"""
        try:
            d = json.loads(self.home_stats) if self.home_stats else {}
        except (json.JSONDecodeError, TypeError):
            d = {}
        if not isinstance(d, dict):
            d = {}
        d.setdefault("population", "2500+")
        d.setdefault("area", "15km²")
        d.setdefault("output", "1200万")
        d.setdefault("satisfaction", "98%")
        return d

    @property
    def labels_dict(self):
        """解析 KPI 标签 JSON；缺失键用默认中文标签补全（模型级兜底，防模板硬编码）。"""
        default_labels = {
            "population": "常住人口",
            "area": "村庄面积",
            "output": "年农业产值",
            "satisfaction": "村民满意度",
        }
        try:
            d = json.loads(self.stat_labels) if self.stat_labels else {}
        except (json.JSONDecodeError, TypeError):
            d = {}
        if not isinstance(d, dict):
            d = {}
        for k, v in default_labels.items():
            d.setdefault(k, v)
        return d


def ensure_site_config_columns(db):
    """自愈式加列：比对 ``site_config`` 表列集合与 ``SiteConfig`` 模型列集合，缺失则 ALTER 补齐并回填默认值。

    比对对象直接取自模型定义（``SiteConfig.__table__.columns``），因此新增字段
    （如 ``hero_title``）无需手工维护列清单，模型一改即自动自愈。

    仅在旧库未执行迁移脚本时兜底；幂等，可重复运行。须在应用上下文（app_context）内调用。
    """
    from sqlalchemy import inspect as sa_inspect, text

    try:
        inspector = sa_inspect(db.engine)
        existing_cols = {c["name"] for c in inspector.get_columns("site_config")}
    except Exception:
        # 表不存在时 db.create_all 已建好带新列的表，无需处理
        return

    model_cols = {c.name for c in SiteConfig.__table__.columns}
    missing_cols = [c for c in model_cols if c not in existing_cols]
    if not missing_cols:
        return

    # 先加列（ALTER 后立即提交，使后续模型查询可见新列）
    with db.engine.begin() as conn:
        for col in missing_cols:
            conn.execute(text(f"ALTER TABLE site_config ADD COLUMN {col} TEXT"))

    # 再用默认值回填为 NULL 的列（仅当真实数据行存在时）
    cfg = SiteConfig.query.first()
    if cfg is not None:
        defaults = SiteConfig.default_values()
        for col in missing_cols:
            if not getattr(cfg, col, None):
                setattr(cfg, col, defaults.get(col, ""))
        db.session.commit()
    print(f"[自愈] 已为 site_config 补齐缺失列并回填: {missing_cols}")


class FriendLink(db.Model):
    """友情链接（前台页脚渲染）。"""

    __tablename__ = "friend_links"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # 链接名称
    url = db.Column(db.String(255), default="")  # 跳转地址
    logo_url = db.Column(db.String(255), default="")  # 站点图标（可选）
    description = db.Column(db.Text, default="")  # 备注
    sort_order = db.Column(db.Integer, default=0)  # 排序
    is_active = db.Column(db.Boolean, default=True)  # 是否展示
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class VillageHighlight(db.Model):
    """村情·乡村特色卡片（前台可配）。"""

    __tablename__ = "village_highlights"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)  # 卡片标题
    description = db.Column(db.Text, default="")  # 文案
    icon = db.Column(db.String(50), default="fas fa-leaf")  # FontAwesome 图标类名
    sort_order = db.Column(db.Integer, default=0)  # 排序


class VillageStat(db.Model):
    """村情·村庄信息指标（前台可配）。"""

    __tablename__ = "village_stats"
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(100), nullable=False)  # 指标名
    value = db.Column(db.String(100), default="")  # 指标值
    group_name = db.Column(db.String(50), default="其他")  # 分组
    sort_order = db.Column(db.Integer, default=0)  # 排序
