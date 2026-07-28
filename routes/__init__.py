"""
应用工厂：创建 Flask app 并注册蓝图
"""

import os
from flask import Flask
from flask_cors import CORS
from models import db

import _compat  # noqa: F401 — Windows + asyncio 兼容桩

from core.logging_config import setup_logging
from core.responses import register_error_handlers


def create_app(config_name="default"):
    setup_logging()

    app = Flask(__name__, static_folder="../static", template_folder="../templates")

    # 配置
    from config import (
        SQLALCHEMY_DATABASE_URI,
        UPLOAD_FOLDER,
        BACKUP_FOLDER,
        SECRET_KEY,
        TINYMCE_API_KEY,
    )

    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    app.config["TINYMCE_API_KEY"] = TINYMCE_API_KEY

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(BACKUP_FOLDER, exist_ok=True)

    db.init_app(app)
    CORS(app)

    # Flasgger (Swagger UI) - 可选依赖
    try:
        from flasgger import Swagger

        swagger_template = {
            "swagger": "2.0",
            "info": {
                "title": "乡村记忆系统 API",
                "description": "美丽乡村信息平台 REST API\n\n"
                "## 认证\n"
                "- 使用 `/login` 登录后获取 session\n"
                "- 管理接口需要 `role=admin`\n\n"
                "## 数据格式\n"
                "- 请求/响应格式: JSON\n"
                "- 日期: YYYY-MM-DD\n"
                "- 时间戳: ISO 8601",
                "version": "2.0.0",
            },
            "basePath": "/",
            "tags": [
                {"name": "新闻", "description": "新闻动态 CRUD"},
                {"name": "村情", "description": "乡村概况"},
                {"name": "政务", "description": "政务公开"},
                {"name": "服务", "description": "便民服务"},
                {"name": "留言", "description": "互动交流"},
                {"name": "分类", "description": "新闻分类"},
                {"name": "Logo/轮播", "description": "网站品牌设置"},
                {"name": "上传", "description": "文件上传"},
                {"name": "记忆", "description": "怀旧记录"},
                {"name": "媒体", "description": "媒体文件管理"},
                {"name": "通知", "description": "系统通知"},
                {"name": "认证", "description": "登录注册"},
                {"name": "管理后台", "description": "管理员接口"},
            ],
        }
        Swagger(app, template=swagger_template)
    except ImportError:
        pass

    # 注册蓝图
    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.api import api_bp
    from routes.memories import memories_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(memories_bp)
    app.register_blueprint(admin_bp)

    # 全局模板变量注入：站点配置 / 当前时间 / 友情链接
    @app.context_processor
    def inject_site_globals():
        from datetime import datetime

        site_config = None
        friend_links = []
        try:
            from models import SiteConfig, FriendLink

            site_config = SiteConfig.get()
            friend_links = (
                FriendLink.query.filter_by(is_active=True)
                .order_by(FriendLink.sort_order, FriendLink.id)
                .all()
            )
        except Exception:
            # 任何异常（表缺失/未初始化）都兜底，避免页面 500
            site_config = None
            friend_links = []
        return dict(site_config=site_config, now=datetime.now(), friend_links=friend_links)

    # 全局错误处理器（仅影响未匹配路由/未捕获异常）
    register_error_handlers(app)

    # 关闭数据库连接
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()

    # favicon.ico 路由 - 消除浏览器404请求
    @app.route("/favicon.ico")
    def favicon():
        return "", 204

    # 自愈式加列：确保 site_config 表含 SiteConfig 模型定义的全部列（向前兼容旧库）。
    # 比对直接取自模型定义，新增字段（如 hero_title）无需手工维护列清单；幂等、可重复运行。
    # 放在 app factory 内，使测试 / 脚本通过 create_app() 创建应用时也能自动补齐，
    # 避免「模型已加列但旧库无列」导致的 OperationalError。
    try:
        with app.app_context():
            db.create_all()
            from models import ensure_site_config_columns

            ensure_site_config_columns(db)
    except Exception as _heal_err:  # noqa: BLE001
        app.logger.warning(f"自愈式加列跳过（不影响启动）: {_heal_err}")

    return app
