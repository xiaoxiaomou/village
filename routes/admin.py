"""
管理后台蓝图：所有 /admin 页面和 /api/admin/* 端点
"""

from flask import (
    Blueprint,
    request,
    session,
    render_template,
    redirect,
    url_for,
    flash,
    jsonify,
)
from werkzeug.security import check_password_hash
from models import (
    db,
    User,
    News,
    Category,
    Service,
    Government,
    VillageInfo,
    Memory,
    People,
    Tag,
)
from models import (
    Message,
    VillageLogo,
    VillageCarousel,
    PendingUser,
    MediaFile,
    AuditLog,
    Notification,
)
from datetime import datetime
import logging

admin_bp = Blueprint("admin", __name__)
logger = logging.getLogger(__name__)


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


# ═══ 页面路由 ═══


@admin_bp.route("/admin")
def admin_dashboard():
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("auth.login"))
    return render_template("admin_dashboard.html")


@admin_bp.route("/admin/logo")
@admin_required
def admin_logo_page():
    return render_template("admin_logo.html")


@admin_bp.route("/admin/carousel")
@admin_required
def admin_carousel_page():
    return render_template("admin_carousel.html")


@admin_bp.route("/admin/news", methods=["GET", "POST"])
@admin_required
def admin_news():
    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        new_news = News(title=title, content=content)
        db.session.add(new_news)
        db.session.commit()
        flash("新闻添加成功")
        return redirect(url_for("admin.admin_news"))
    news_list = News.query.order_by(News.create_time.desc()).all()
    return render_template("admin_news.html", news_list=news_list)


@admin_bp.route("/admin/news/<int:news_id>", methods=["PUT", "DELETE"])
@admin_required
def edit_news(news_id):
    news = News.query.get(news_id)
    if not news:
        return jsonify({"msg": "新闻不存在"}), 404
    if request.method == "PUT":
        data = request.json
        news.title = data.get("title", news.title)
        news.content = data.get("content", news.content)
        db.session.commit()
        return jsonify(
            {
                "msg": "新闻更新成功",
                "news": {"id": news.id, "title": news.title, "content": news.content},
            }
        )
    db.session.delete(news)
    db.session.commit()
    return jsonify({"msg": "新闻已删除"})


@admin_bp.route("/admin/categories", methods=["GET", "POST"])
@admin_required
def admin_categories():
    if request.method == "POST":
        data = request.json
        name = data.get("name")
        if not name:
            return jsonify({"msg": "分类名称不能为空"}), 400
        cat = Category(name=name)
        db.session.add(cat)
        db.session.commit()
        return jsonify(
            {"msg": "分类添加成功", "category": {"id": cat.id, "name": cat.name}}
        ), 201
    categories = Category.query.order_by(Category.id).all()
    return jsonify([{"id": c.id, "name": c.name} for c in categories])


@admin_bp.route("/admin/categories/<int:category_id>", methods=["PUT", "DELETE"])
@admin_required
def edit_category(category_id):
    cat = Category.query.get(category_id)
    if not cat:
        return jsonify({"msg": "分类不存在"}), 404
    if request.method == "PUT":
        data = request.json
        cat.name = data.get("name", cat.name)
        db.session.commit()
        return jsonify(
            {"msg": "分类更新成功", "category": {"id": cat.id, "name": cat.name}}
        )
    # DELETE - check if news use this category
    count = News.query.filter_by(category_id=category_id).count()
    if count > 0:
        return jsonify({"msg": f"该分类下还有{count}条新闻，无法删除"}), 400
    db.session.delete(cat)
    db.session.commit()
    return jsonify({"msg": "分类删除成功"})


@admin_bp.route("/admin/categories/page")
@admin_required
def admin_categories_page():
    return render_template("admin_simple.html", title="分类管理")


@admin_bp.route("/admin/messages")
@admin_required
def admin_messages_page():
    return render_template("admin_messages.html")


@admin_bp.route("/admin/messages/data", methods=["GET", "POST"])
@admin_required
def admin_messages():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        name = (data.get("name") or "").strip()
        content = (data.get("content") or "").strip()
        if not name or not content:
            return jsonify({"msg": "姓名和内容不能为空"}), 400
        msg = Message(name=name, contact=data.get("contact", ""), content=content)
        db.session.add(msg)
        db.session.commit()
        return jsonify(
            {
                "msg": "留言添加成功",
                "message": {"id": msg.id, "name": msg.name, "content": msg.content},
            }
        ), 201
    msgs = Message.query.order_by(Message.create_time.desc()).all()
    return jsonify(
        [
            dict(
                id=m.id,
                name=m.name,
                contact=m.contact,
                content=m.content,
                reply=m.reply,
                create_time=str(m.create_time) if m.create_time else None,
            )
            for m in msgs
        ]
    )


@admin_bp.route("/admin/messages/data/<int:msg_id>/reply", methods=["POST"])
@admin_required
def reply_message(msg_id):
    data = request.get_json(silent=True) or {}
    reply_content = (data.get("reply") or "").strip()
    if not reply_content:
        return jsonify({"msg": "回复内容不能为空"}), 400
    msg = Message.query.get(msg_id)
    if not msg:
        return jsonify({"msg": "留言不存在"}), 404
    msg.reply = reply_content
    db.session.commit()
    return jsonify({"msg": "回复成功", "message": {"id": msg.id, "reply": msg.reply}})


@admin_bp.route("/admin/users", methods=["GET", "POST"])
@admin_required
def admin_users():
    if request.method == "POST":
        # 创建新用户
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "user")
        if not username or not password:
            flash("用户名和密码不能为空")
            return redirect(url_for("admin.admin_users"))
        if len(password) < 6:
            flash("密码至少6个字符")
            return redirect(url_for("admin.admin_users"))
        # 检查用户名是否已存在
        existing = User.query.filter_by(username=username).first()
        if existing:
            flash("用户名已存在")
            return redirect(url_for("admin.admin_users"))
        new_user = User(username=username, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash(f"用户 {username} 创建成功")
        return redirect(url_for("admin.admin_users"))
    
    users = User.query.order_by(User.create_time.desc()).all()
    users_data = [
        {
            "id": u.id,
            "username": u.username,
            "role": u.role,
            "create_time": str(u.create_time) if u.create_time else None,
        }
        for u in users
    ]
    if request.is_json or (
        request.accept_mimetypes and request.accept_mimetypes.best == "application/json"
    ):
        return jsonify(users_data)
    return render_template("admin_users.html", users=users_data)


@admin_bp.route("/admin/users/<int:uid>", methods=["PUT", "DELETE"])
@admin_required
def edit_user(uid):
    user = User.query.get(uid)
    if not user:
        return jsonify({"msg": "用户不存在"}), 404
    if request.method == "PUT":
        data = request.json
        # 更新用户名
        if data.get("username"):
            # 检查新用户名是否与其他用户冲突
            existing = User.query.filter(User.username == data["username"], User.id != uid).first()
            if existing:
                return jsonify({"msg": "用户名已存在"}), 400
            user.username = data["username"]
        # 更新密码
        if data.get("password"):
            if len(data["password"]) < 6:
                return jsonify({"msg": "密码至少6个字符"}), 400
            user.set_password(data["password"])
        # 更新角色
        if data.get("role"):
            user.role = data["role"]
        db.session.commit()
        return jsonify({"msg": "用户更新成功", "user": {"id": user.id, "username": user.username, "role": user.role}})
    # DELETE
    # 不能删除自己
    if session.get("user") == user.username:
        return jsonify({"msg": "不能删除当前登录用户"}), 400
    db.session.delete(user)
    db.session.commit()
    return jsonify({"msg": "用户已删除"})


@admin_bp.route("/admin/village", methods=["GET", "POST"])
@admin_required
def admin_village():
    if request.method == "POST":
        data = request.get_json(silent=True) or request.form
        title = data.get("title", "")
        content = data.get("content", "")
        if not title or not content:
            if request.is_json:
                return jsonify({"msg": "标题和内容不能为空"}), 400
            flash("标题和内容不能为空")
            return redirect(url_for("admin.admin_village"))
        info = VillageInfo(
            title=title, content=content, image_url=data.get("image_url", "")
        )
        db.session.add(info)
        db.session.commit()
        if request.is_json:
            return jsonify(
                {
                    "msg": "乡村概况添加成功",
                    "village": {"id": info.id, "title": info.title},
                }
            ), 201
        flash("乡村概况添加成功")
        return redirect(url_for("admin.admin_village"))
    infos = VillageInfo.query.order_by(VillageInfo.id.desc()).all()
    if request.is_json or (
        request.accept_mimetypes and request.accept_mimetypes.best == "application/json"
    ):
        return jsonify(
            [
                {
                    "id": i.id,
                    "title": i.title,
                    "content": i.content,
                    "image_url": i.image_url,
                }
                for i in infos
            ]
        )
    return render_template("admin_village.html", village_list=infos)


@admin_bp.route("/admin/village/<int:vid>", methods=["PUT", "DELETE"])
@admin_required
def edit_village(vid):
    info = VillageInfo.query.get(vid)
    if not info:
        return jsonify({"msg": "乡村概况不存在"}), 404
    if request.method == "PUT":
        data = request.json
        info.title = data.get("title", info.title)
        info.content = data.get("content", info.content)
        info.image_url = data.get("image_url", info.image_url)
        db.session.commit()
        return jsonify(
            {"msg": "乡村概况更新成功", "village": {"id": info.id, "title": info.title}}
        )
    db.session.delete(info)
    db.session.commit()
    return jsonify({"msg": "乡村概况已删除"})


@admin_bp.route("/admin/government", methods=["GET", "POST"])
@admin_required
def admin_government():
    if request.method == "POST":
        data = request.get_json(silent=True) or request.form
        title = data.get("title", "")
        if not title:
            return jsonify({"msg": "标题不能为空"}), 400 if request.is_json else (
                flash("标题不能为空"),
                redirect(url_for("admin.admin_government")),
            )
        gov = Government(title=title, file_url=data.get("file_url", ""))
        db.session.add(gov)
        db.session.commit()
        if request.is_json:
            return jsonify(
                {
                    "msg": "政务信息添加成功",
                    "government": {"id": gov.id, "title": gov.title},
                }
            ), 201
        flash("政务信息添加成功")
        return redirect(url_for("admin.admin_government"))
    govs = Government.query.order_by(Government.id.desc()).all()
    if request.is_json or (
        request.accept_mimetypes and request.accept_mimetypes.best == "application/json"
    ):
        return jsonify(
            [{"id": g.id, "title": g.title, "file_url": g.file_url} for g in govs]
        )
    return render_template("admin_government.html", government_list=govs)


@admin_bp.route("/admin/government/<int:gov_id>", methods=["PUT", "DELETE"])
@admin_required
def edit_government(gov_id):
    gov = Government.query.get(gov_id)
    if not gov:
        return jsonify({"msg": "政务信息不存在"}), 404
    if request.method == "PUT":
        data = request.json
        gov.title = data.get("title", gov.title)
        gov.file_url = data.get("file_url", gov.file_url)
        db.session.commit()
        return jsonify(
            {
                "msg": "政务信息更新成功",
                "government": {"id": gov.id, "title": gov.title},
            }
        )
    db.session.delete(gov)
    db.session.commit()
    return jsonify({"msg": "政务信息已删除"})


@admin_bp.route("/admin/services", methods=["GET", "POST"])
@admin_required
def admin_services():
    if request.method == "POST":
        data = request.get_json(silent=True) or request.form
        name = (data.get("name", "") or "").strip()
        if not name:
            return jsonify({"msg": "服务名称不能为空"}), 400
        svc = Service(
            name=name,
            description=data.get("description", ""),
            file_url=data.get("file_url", ""),
        )
        db.session.add(svc)
        db.session.commit()
        if request.is_json:
            return jsonify(
                {"msg": "服务添加成功", "service": {"id": svc.id, "name": svc.name}}
            ), 201
        flash("服务添加成功")
        return redirect(url_for("admin.admin_services"))
    services = Service.query.order_by(Service.id.desc()).all()
    if request.is_json or (
        request.accept_mimetypes and request.accept_mimetypes.best == "application/json"
    ):
        return jsonify(
            [
                {"id": s.id, "name": s.name, "description": s.description}
                for s in services
            ]
        )
    return render_template("admin_services.html", services=services)


@admin_bp.route("/admin/services/<int:service_id>", methods=["PUT", "DELETE"])
@admin_required
def edit_services(service_id):
    svc = Service.query.get(service_id)
    if not svc:
        return jsonify({"msg": "服务不存在"}), 404
    if request.method == "PUT":
        data = request.json
        svc.name = data.get("name", svc.name)
        svc.description = data.get("description", svc.description)
        svc.file_url = data.get("file_url", svc.file_url)
        db.session.commit()
        return jsonify(
            {"msg": "服务更新成功", "service": {"id": svc.id, "name": svc.name}}
        )
    db.session.delete(svc)
    db.session.commit()
    return jsonify({"msg": "服务已删除"})


# ═══ Logo 管理 ═══


@admin_bp.route("/admin/logo", methods=["GET", "POST"])
@admin_required
def admin_logo():
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
            }
        )
    return jsonify({"msg": "暂无Logo", "logo": None}), 200


# ═══ 用户审核 ═══


@admin_bp.route("/api/pending-users", methods=["GET"])
@admin_required
def api_pending_users():
    pending = (
        PendingUser.query.filter_by(status="pending")
        .order_by(PendingUser.created_at.desc())
        .all()
    )
    return jsonify(
        [
            {
                "id": p.id,
                "username": p.username,
                "email": p.email,
                "phone": p.phone,
                "nickname": p.nickname,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in pending
        ]
    )


@admin_bp.route("/api/pending-users/<int:uid>", methods=["PUT"])
@admin_required
def api_review_user(uid):
    pending = PendingUser.query.get(uid)
    if not pending:
        return jsonify({"msg": "申请不存在"}), 404
    data = request.json
    action = data.get("action")
    if action not in ("approve", "reject"):
        return jsonify({"msg": "无效操作"}), 400
    if action == "approve":
        pending.status = "approved"
        existing = User.query.filter_by(username=pending.username).first()
        if not existing:
            new_user = User(username=pending.username, role="user")
            new_user.password_hash = pending.password_hash
            db.session.add(new_user)
        pending.reviewed_at = datetime.utcnow()
        pending.review_comment = data.get("comment", "")
    else:
        pending.status = "rejected"
        pending.reviewed_at = datetime.utcnow()
        pending.admin_note = data.get("note", "")
        pending.review_comment = data.get("comment", "")
    log = AuditLog(
        action="review",
        target_type="user",
        target_id=pending.id,
        detail=f'管理员审核{"通过" if action == "approve" else "拒绝"}用户 "{pending.username}"',
        ip_address=request.remote_addr,
    )
    db.session.add(log)
    db.session.commit()
    return jsonify({"msg": f"用户{'已批准' if action == 'approve' else '已拒绝'}"})


# ═══ 管理员 API ═══


@admin_bp.route("/api/admin/users")
@admin_required
def api_admin_users():
    users = User.query.order_by(User.id).all()
    return jsonify(
        [
            {
                "id": u.id,
                "username": u.username,
                "role": u.role,
                "created_at": u.create_time.isoformat() if u.create_time else None,
            }
            for u in users
        ]
    )


@admin_bp.route("/api/admin/media")
@admin_required
def api_admin_media():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    query = MediaFile.query.order_by(MediaFile.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify(
        {
            "data": [
                {
                    "id": m.id,
                    "title": m.title,
                    "file_url": m.file_url,
                    "file_type": m.file_type,
                    "file_size": m.file_size,
                    "original_name": m.original_name,
                    "username": m.owner.username if m.owner else None,
                    "view_count": m.view_count,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in pagination.items
            ],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": pagination.total,
                "pages": pagination.pages,
            },
        }
    )


@admin_bp.route("/api/admin/logs")
@admin_required
def api_admin_logs():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    query = AuditLog.query.order_by(AuditLog.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify(
        {
            "data": [
                {
                    "id": l.id,
                    "action": l.action,
                    "detail": l.detail,
                    "ip_address": l.ip_address,
                    "created_at": l.created_at.isoformat() if l.created_at else None,
                }
                for l in pagination.items
            ],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": pagination.total,
                "pages": pagination.pages,
            },
        }
    )


@admin_bp.route("/api/admin/stats")
@admin_required
def api_admin_stats():
    return jsonify(
        {
            "users": User.query.count(),
            "memories": Memory.query.count(),
            "news": News.query.count(),
            "media": MediaFile.query.count(),
            "pending_users": PendingUser.query.filter_by(status="pending").count(),
            "unread_notifications": Notification.query.filter_by(is_read=False).count(),
        }
    )


# ═══ 记忆管理 ═══


@admin_bp.route("/admin/memories")
@admin_required
def admin_memories_page():
    """记忆管理页面"""
    return render_template("admin_memories.html")


# ═══ 人物管理 ═══


@admin_bp.route("/admin/people")
@admin_required
def admin_people_page():
    """人物档案管理页面"""
    return render_template("admin_people.html")


@admin_bp.route("/api/admin/people", methods=["GET", "POST"])
@admin_required
def api_admin_people():
    if request.method == "POST":
        data = request.json
        person = People(
            name=data.get("name", ""),
            relation=data.get("relation", ""),
            bio=data.get("bio", ""),
        )
        db.session.add(person)
        db.session.commit()
        return jsonify(
            {
                "msg": "人物创建成功",
                "person": {
                    "id": person.id,
                    "name": person.name,
                },
            }
        ), 201
    people = People.query.order_by(People.name).all()
    return jsonify(
        [
            {
                "id": p.id,
                "name": p.name,
                "relation": p.relation,
                "bio": p.bio,
                "photo_url": p.photo_url,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in people
        ]
    )


@admin_bp.route("/api/admin/people/<int:pid>", methods=["PUT", "DELETE"])
@admin_required
def api_admin_person_detail(pid):
    person = People.query.get(pid)
    if not person:
        return jsonify({"msg": "人物不存在"}), 404
    if request.method == "PUT":
        data = request.json
        person.name = data.get("name", person.name)
        person.relation = data.get("relation", person.relation)
        person.bio = data.get("bio", person.bio)
        person.photo_url = data.get("photo_url", person.photo_url)
        db.session.commit()
        return jsonify({"msg": "人物更新成功"})
    db.session.delete(person)
    db.session.commit()
    return jsonify({"msg": "人物已删除"})


# ═══ 标签管理 ═══


@admin_bp.route("/admin/tags")
@admin_required
def admin_tags_page():
    """标签管理页面"""
    return render_template("admin_tags.html")


@admin_bp.route("/api/admin/tags", methods=["GET", "POST"])
@admin_required
def api_admin_tags():
    if request.method == "POST":
        data = request.json
        tag = Tag(
            name=data.get("name", ""),
            category=data.get("category", "general"),
            color=data.get("color", "#4a90d9"),
        )
        db.session.add(tag)
        db.session.commit()
        return jsonify(
            {
                "msg": "标签创建成功",
                "tag": {
                    "id": tag.id,
                    "name": tag.name,
                },
            }
        ), 201
    tags = Tag.query.order_by(Tag.name).all()
    return jsonify(
        [
            {
                "id": t.id,
                "name": t.name,
                "category": t.category,
                "color": t.color,
                "memory_count": t.memory_count,
            }
            for t in tags
        ]
    )


@admin_bp.route("/api/admin/tags/<int:tid>", methods=["PUT", "DELETE"])
@admin_required
def api_admin_tag_detail(tid):
    tag = Tag.query.get(tid)
    if not tag:
        return jsonify({"msg": "标签不存在"}), 404
    if request.method == "PUT":
        data = request.json
        tag.name = data.get("name", tag.name)
        tag.category = data.get("category", tag.category)
        tag.color = data.get("color", tag.color)
        db.session.commit()
        return jsonify({"msg": "标签更新成功"})
    db.session.delete(tag)
    db.session.commit()
    return jsonify({"msg": "标签已删除"})
