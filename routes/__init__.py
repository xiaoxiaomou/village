"""
应用工厂：创建 Flask app 并注册蓝图
"""

import os
from flask import Flask
from flask_cors import CORS
from models import db

import _compat  # noqa: F401 — Windows + asyncio 兼容桩


def create_app(config_name="default"):
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

    # 关闭数据库连接
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()

    # favicon.ico 路由 - 消除浏览器404请求
    @app.route("/favicon.ico")
    def favicon():
        return "", 204

    return app
