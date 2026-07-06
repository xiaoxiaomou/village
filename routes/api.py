"""
API 蓝图：公共 JSON REST API
新闻、村情、政务、服务、留言、分类、Logo、轮播图、上传、统计
"""

from flask import Blueprint, jsonify, request, session
from models import db, User, News, VillageInfo, Government, Service, Message, Category
from models import VillageLogo, VillageCarousel, MediaFile, AuditLog
from datetime import datetime
import os
import json
import logging

api_bp = Blueprint("api", __name__)
logger = logging.getLogger(__name__)


def login_required(f):
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return jsonify({"msg": "未登录"}), 401
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return jsonify({"msg": "未登录"}), 401
        if session.get("role") != "admin":
            return jsonify({"msg": "无权限"}), 403
        return f(*args, **kwargs)

    return decorated_function


# ─── 新闻 API ───


@api_bp.route("/api/news")
def get_news():
    """
    新闻列表 API
    支持分页、全文搜索、分类筛选
    ---
    tags:
      - 新闻
    parameters:
      - name: page
        in: query
        type: integer
        default: 1
        description: 页码
      - name: per_page
        in: query
        type: integer
        default: 10
        description: 每页条数
      - name: search
        in: query
        type: string
        description: 搜索关键词
      - name: category_id
        in: query
        type: integer
        description: 分类ID
    responses:
      200:
        description: 新闻列表(含分页)
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    search = request.args.get("search", "", type=str)
    category_id = request.args.get("category_id", type=int)

    query = News.query.order_by(News.create_time.desc())
    if search:
        query = query.filter(
            db.or_(News.title.contains(search), News.content.contains(search))
        )
    if category_id:
        query = query.filter_by(category_id=category_id)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    news_list = [
        {
            "id": n.id,
            "title": n.title,
            "content": n.content,
            "create_time": str(n.create_time) if n.create_time else None,
            "author": n.author,
            "category_id": n.category_id,
        }
        for n in pagination.items
    ]

    return jsonify(
        {
            "data": news_list,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": pagination.total,
                "pages": (pagination.total + per_page - 1) // per_page,
            },
        }
    )


@api_bp.route("/api/news/<int:news_id>")
def get_news_detail(news_id):
    news = News.query.get(news_id)
    if not news:
        return jsonify({"msg": "新闻不存在"}), 404
    # 增加访问量 - 使用 update 而不是直接设置字段
    try:
        db.session.execute(
            db.text(
                "UPDATE news SET view_count = COALESCE(view_count, 0) + 1 WHERE id=:id"
            ),
            {"id": news_id},
        )
        db.session.commit()
    except Exception:
        pass
    result = {c.name: getattr(news, c.name) for c in news.__table__.columns}
    for k in ("create_time", "update_time"):
        if k in result and result[k]:
            result[k] = str(result[k])
    return jsonify(result)


# ─── 服务 API ───


@api_bp.route("/api/services")
def get_services():
    services = Service.query.order_by(Service.id.desc()).all()
    return jsonify(
        [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "url": s.file_url,
            }
            for s in services
        ]
    )


# ─── 村情 API ───


@api_bp.route("/api/village")
def get_village_info():
    info = VillageInfo.query.order_by(VillageInfo.id.desc()).first()
    if info:
        return jsonify(
            {
                "id": info.id,
                "title": info.title,
                "content": info.content,
                "image_url": info.image_url,
            }
        )
    return jsonify(None)


# ─── 政务 API ───


@api_bp.route("/api/government")
def get_government_info():
    govs = Government.query.order_by(Government.id.desc()).all()
    return jsonify(
        [
            {"id": g.id, "title": g.title, "file_url": g.file_url, "content": g.content}
            for g in govs
        ]
    )


# ─── 留言 API ───


@api_bp.route("/api/messages", methods=["GET", "POST"])
def messages():
    if request.method == "POST":
        # 登录验证
        if "user" not in session:
            return jsonify({"msg": "未登录"}), 401
        data = request.get_json(silent=True) or {}
        name = (data.get("name") or "").strip()
        content = (data.get("content") or "").strip()
        if not name or not content:
            return jsonify({"msg": "姓名和内容不能为空"}), 400
        msg = Message(name=name, content=content, contact=data.get("contact", ""))
        db.session.add(msg)
        db.session.commit()
        return jsonify(
            {
                "msg": "留言提交成功",
                "data": {"id": msg.id, "name": msg.name, "content": msg.content},
            }
        ), 201

    msgs = Message.query.order_by(Message.create_time.desc()).all()
    return jsonify(
        [
            {
                "id": m.id,
                "name": m.name,
                "content": m.content,
                "reply": m.reply,
                "create_time": str(m.create_time) if m.create_time else None,
            }
            for m in msgs
        ]
    )


# ─── 分类 API ───


@api_bp.route("/api/categories")
def get_categories():
    categories = Category.query.order_by(Category.id).all()
    return jsonify([{"id": c.id, "name": c.name} for c in categories])


# ─── Logo API ───


@api_bp.route("/api/logo", methods=["GET", "POST"])
@admin_required
def get_village_logo():
    if request.method == "POST":
        data = request.json
        name = data.get("name")
        logo_url = data.get("logo_url")
        description = data.get("description", "")
        if not name or not logo_url:
            return jsonify({"msg": "乡村名称和Logo不能为空"}), 400
        existing_logo = VillageLogo.query.filter_by(is_active=True).first()
        if existing_logo:
            existing_logo.name = name
            existing_logo.logo_url = logo_url
            existing_logo.description = description
            existing_logo.update_time = datetime.utcnow()
            db.session.commit()
            return jsonify(
                {
                    "msg": "Logo更新成功",
                    "logo": {
                        "id": existing_logo.id,
                        "name": existing_logo.name,
                        "logo_url": existing_logo.logo_url,
                        "description": existing_logo.description,
                    },
                }
            )
        new_logo = VillageLogo(name=name, logo_url=logo_url, description=description)
        db.session.add(new_logo)
        db.session.commit()
        return jsonify(
            {
                "msg": "Logo创建成功",
                "logo": {
                    "id": new_logo.id,
                    "name": new_logo.name,
                    "logo_url": new_logo.logo_url,
                    "description": new_logo.description,
                },
            }
        ), 201

    logo = VillageLogo.query.filter_by(is_active=True).first()
    if logo:
        return jsonify(
            {
                "id": logo.id,
                "name": logo.name,
                "logo_url": logo.logo_url,
                "description": logo.description,
                "create_time": logo.create_time.isoformat()
                if logo.create_time
                else None,
                "update_time": logo.update_time.isoformat()
                if logo.update_time
                else None,
            }
        )
    return jsonify({"msg": "暂无Logo", "logo": None}), 200


# ─── 轮播图 API ───


@api_bp.route("/api/carousel", methods=["GET", "POST"])
def get_village_carousel():
    if request.method == "POST":
        if "user" not in session or session.get("role") != "admin":
            return jsonify({"msg": "无权限"}), 403
        data = request.json
        title = data.get("title")
        image_url = data.get("image_url")
        if not title or not image_url:
            return jsonify({"msg": "标题和图片不能为空"}), 400
        new_carousel = VillageCarousel(
            title=title,
            image_url=image_url,
            description=data.get("description", ""),
            link_url=data.get("link_url", ""),
            sort_order=data.get("sort_order", 0),
        )
        db.session.add(new_carousel)
        db.session.commit()
        return jsonify(
            {
                "msg": "轮播图添加成功",
                "carousel": {
                    "id": new_carousel.id,
                    "title": new_carousel.title,
                    "image_url": new_carousel.image_url,
                },
            }
        ), 201

    is_admin = session.get("role") == "admin"
    if is_admin:
        carousels = VillageCarousel.query.order_by(VillageCarousel.sort_order).all()
        return jsonify(
            [
                {
                    "id": c.id,
                    "title": c.title,
                    "image_url": c.image_url,
                    "description": c.description,
                    "link_url": c.link_url,
                    "sort_order": c.sort_order,
                    "is_active": c.is_active,
                    "create_time": c.create_time.isoformat() if c.create_time else None,
                    "update_time": c.update_time.isoformat() if c.update_time else None,
                }
                for c in carousels
            ]
        )
    else:
        carousels = (
            VillageCarousel.query.filter_by(is_active=True)
            .order_by(VillageCarousel.sort_order)
            .all()
        )
        return jsonify(
            [
                {
                    "id": c.id,
                    "title": c.title,
                    "image_url": c.image_url,
                    "description": c.description,
                    "link_url": c.link_url,
                    "sort_order": c.sort_order,
                }
                for c in carousels
            ]
        )


@api_bp.route("/api/carousel/<int:carousel_id>", methods=["PUT", "DELETE"])
def edit_carousel_api(carousel_id):
    if session.get("role") != "admin":
        return jsonify({"msg": "无权限"}), 403
    carousel = VillageCarousel.query.get_or_404(carousel_id)
    if request.method == "PUT":
        data = request.json
        carousel.title = data.get("title", carousel.title)
        carousel.image_url = data.get("image_url", carousel.image_url)
        carousel.description = data.get("description", carousel.description)
        carousel.link_url = data.get("link_url", carousel.link_url)
        carousel.sort_order = data.get("sort_order", carousel.sort_order)
        carousel.is_active = data.get("is_active", carousel.is_active)
        carousel.update_time = datetime.utcnow()
        db.session.commit()
        return jsonify(
            {
                "msg": "轮播图更新成功",
                "carousel": {
                    "id": carousel.id,
                    "title": carousel.title,
                    "image_url": carousel.image_url,
                },
            }
        )
    db.session.delete(carousel)
    db.session.commit()
    return jsonify({"msg": "轮播图删除成功"})


@api_bp.route("/api/carousel/reorder", methods=["POST"])
def reorder_carousel_api():
    if session.get("role") != "admin":
        return jsonify({"msg": "无权限"}), 403
    data = request.json
    for item in data.get("carousel_orders", []):
        carousel = VillageCarousel.query.get(item["id"])
        if carousel:
            carousel.sort_order = item["sort_order"]
    db.session.commit()
    return jsonify({"msg": "轮播图排序更新成功"})


# ─── 文件上传 API ───


@api_bp.route("/api/upload", methods=["POST"])
def upload_file():
    if session.get("role") != "admin":
        return jsonify({"msg": "无权限"}), 403
    if "file" not in request.files:
        return jsonify({"msg": "没有文件"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"msg": "没有选择文件"}), 400
    if file:
        import uuid
        from werkzeug.utils import secure_filename
        from flask import current_app

        filename = secure_filename(file.filename)
        file_ext = filename.rsplit(".", 1)[1].lower() if "." in filename else ""
        unique_filename = (
            f"{uuid.uuid4().hex}.{file_ext}" if file_ext else str(uuid.uuid4().hex)
        )
        allowed_extensions = {
            "txt",
            "pdf",
            "png",
            "jpg",
            "jpeg",
            "gif",
            "doc",
            "docx",
            "xls",
            "xlsx",
        }
        if file_ext not in allowed_extensions:
            return jsonify({"msg": "不支持的文件类型"}), 400
        file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_filename)
        file.save(file_path)
        return jsonify(
            {
                "msg": "文件上传成功",
                "filename": unique_filename,
                "original_name": filename,
                "url": f"/download/{unique_filename}",
            }
        )
    return jsonify({"msg": "上传失败"}), 500


@api_bp.route("/api/upload/image", methods=["POST"])
def upload_image():
    if session.get("role") != "admin":
        return jsonify({"msg": "无权限"}), 403
    if "image" not in request.files:
        return jsonify({"msg": "没有图片"}), 400
    file = request.files["image"]
    if file.filename == "":
        return jsonify({"msg": "没有选择图片"}), 400
    if file:
        import uuid
        from werkzeug.utils import secure_filename
        from flask import current_app

        filename = secure_filename(file.filename)
        file_ext = filename.rsplit(".", 1)[1].lower() if "." in filename else ""
        allowed_extensions = {"png", "jpg", "jpeg", "gif", "webp"}
        if file_ext not in allowed_extensions:
            return jsonify(
                {"msg": "不支持的图片格式，仅支持 PNG, JPG, JPEG, GIF, WebP"}
            ), 400
        max_size = 5 * 1024 * 1024
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)
        if file_size > max_size:
            return jsonify({"msg": "图片大小不能超过5MB"}), 400
        unique_filename = f"carousel_{uuid.uuid4().hex}.{file_ext}"
        file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_filename)
        file.save(file_path)
        try:
            from PIL import Image

            with Image.open(file_path) as img:
                logger.info(f"上传图片尺寸: {img.size[0]}x{img.size[1]}")
        except Exception:
            pass
        return jsonify(
            {
                "msg": "图片上传成功",
                "filename": unique_filename,
                "url": f"/uploads/{unique_filename}",
                "size": file_size,
            }
        )
    return jsonify({"msg": "上传失败"}), 500


# ─── 统计 API ───


@api_bp.route("/api/stats")
def get_stats():
    if session.get("role") != "admin":
        return jsonify({"msg": "无权限"}), 403
    from models import Memory, MediaFile, PendingUser, Notification

    stats = {
        "news_count": News.query.count(),
        "message_count": Message.query.count(),
        "unread_message_count": Message.query.filter(
            db.or_(Message.reply.is_(None), Message.reply == "")
        ).count(),
        "service_count": Service.query.count(),
        "government_count": Government.query.count(),
        "user_count": User.query.count(),
        "recent_news_count": 0,
        "recent_message_count": 0,
    }
    # 最近7天
    stats["users"] = stats["user_count"]
    stats["memories"] = Memory.query.count()
    stats["media"] = MediaFile.query.count()
    stats["pending_users"] = PendingUser.query.filter_by(status="pending").count()
    stats["unread_notifications"] = Notification.query.filter_by(is_read=False).count()
    return jsonify(stats)


# ─── 首页公开统计 API ───
@api_bp.route("/api/home/stats")
def get_home_stats():
    """首页公开统计数据"""
    from models import User, Memory, News, Service

    return jsonify(
        {
            "population": "2500+",
            "area": "15km²",
            "output": "1200万",
            "satisfaction": "98%",
            "users": User.query.count(),
            "memories": Memory.query.count(),
            "news": News.query.count(),
            "services": Service.query.count(),
        }
    )


# ⚠️ 注意：User 导入需要放在这里避免循环依赖
