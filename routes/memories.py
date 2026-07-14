"""
记忆蓝图：怀旧记录、时间轴、人物档案、标签、备份
包含所有记忆相关的页面路由和 JSON API
"""

from flask import Blueprint, jsonify, request, session, render_template, abort
from models import (
    db,
    Memory,
    Tag,
    MemoryTag,
    People,
    Backup,
    MediaFile,
    Notification,
    AuditLog,
    PendingUser,
    User,
)
from datetime import datetime, date
import json
import collections
import os
import logging

memories_bp = Blueprint("memories", __name__)
logger = logging.getLogger(__name__)


# ═══ 辅助函数 ═══


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


def _parse_date(value):
    if value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
    return None


def _filter_by_tag(query, tag_filter):
    """按标签筛选记忆。tag_filter 可以是标签名或标签 id。"""
    if not tag_filter:
        return query
    query = query.join(MemoryTag).join(Tag)
    if str(tag_filter).isdigit():
        return query.filter(MemoryTag.tag_id == int(tag_filter))
    return query.filter(Tag.name == tag_filter)


def _sync_memory_tags(memory_id, tag_ids):
    """用 tag_ids（标签 id 列表）重建记忆与标签的关联，供筛选使用。"""
    MemoryTag.query.filter_by(memory_id=memory_id).delete()
    if isinstance(tag_ids, list):
        for t in tag_ids:
            try:
                tid = int(t)
            except (TypeError, ValueError):
                continue
            tag = Tag.query.get(tid)
            if tag:
                db.session.add(
                    MemoryTag(
                        memory_id=memory_id, tag_id=tid, tag_category=tag.category
                    )
                )
    db.session.commit()


def _memory_to_dict(memory):
    return {
        "id": memory.id,
        "title": memory.title,
        "author": memory.author.username if memory.author else None,
        "content": memory.content,
        "reflection": memory.reflection,
        "type": memory.memory_type,
        "date": str(memory.date_recorded) if memory.date_recorded else "",
        "people": ", ".join(memory.get_people()) if memory.get_people() else None,
        "tags": memory.get_tags(),
        "tag_names": memory.get_tags(),
        "photos": memory.get_photos(),
        "video_urls": memory.get_videos(),
        "audio_url": memory.audio_url,
        "thumbnail": memory.thumbnail,
        "locations": memory.get_locations(),
        "is_public": memory.is_public,
        "create_time": memory.create_time.isoformat() if memory.create_time else None,
        "update_time": memory.update_time.isoformat() if memory.update_time else None,
    }


# ═══ 页面路由 ═══


@memories_bp.route("/timeline")
def timeline_page():
    return render_template("timeline.html")


@memories_bp.route("/memories")
def memories_page():
    page = request.args.get("page", 1, type=int)
    per_page = 10
    tag_filter = request.args.get("tag", "", type=str)
    search = request.args.get("search", "", type=str)
    query = Memory.query.order_by(Memory.create_time.desc())
    query = _filter_by_tag(query, tag_filter)
    if search:
        query = query.filter(
            db.or_(Memory.title.contains(search), Memory.content.contains(search))
        )
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    memories = pagination.items
    tags = Tag.query.all()
    mem_ids = [m.id for m in memories]
    tag_name_map = {}
    if mem_ids:
        rows = (
            db.session.query(MemoryTag.memory_id, Tag.name)
            .join(Tag, Tag.id == MemoryTag.tag_id)
            .filter(MemoryTag.memory_id.in_(mem_ids))
            .all()
        )
        for mid, nm in rows:
            tag_name_map.setdefault(mid, []).append(nm)
    for m in memories:
        m.tag_names = tag_name_map.get(m.id, [])
        m.date = str(m.date_recorded) if m.date_recorded else ""
        m.type = m.memory_type
        m.people = ", ".join(m.get_people()) if m.get_people() else ""
        m.feeling = m.reflection
        m.photo_urls_list = m.get_photos()
        m.video_urls_list = m.get_videos()
    return render_template(
        "memories.html",
        memories=memories,
        tags=tags,
        page=page,
        total_pages=pagination.pages,
        tag=tag_filter,
    )


@memories_bp.route("/memories/new")
def new_memory_page():
    tags = Tag.query.all()
    return render_template("new_memory.html", tags=tags)


@memories_bp.route("/memories/<int:mid>")
def memory_detail_page(mid):
    memory = Memory.query.get_or_404(mid)
    memory_data = {
        "id": memory.id,
        "title": memory.title,
        "content": memory.content,
        "date": str(memory.date_recorded) if memory.date_recorded else "",
        "type": memory.memory_type,
        "people": ", ".join(memory.get_people()) if memory.get_people() else "",
        "feeling": memory.reflection,
        "photo_urls_list": memory.get_photos(),
        "video_urls_list": memory.get_videos(),
        "audio_url": memory.audio_url,
        "author": memory.author.username if memory.author else None,
        "tags": memory.get_tags(),
        "create_time": memory.create_time.isoformat() if memory.create_time else None,
    }
    return render_template("memory_detail.html", memory=memory_data)


@memories_bp.route("/memories/<int:mid>/edit")
def edit_memory_page(mid):
    memory = Memory.query.get_or_404(mid)
    tags = Tag.query.all()
    memory.tag_names = memory.get_tags()
    memory.date = str(memory.date_recorded) if memory.date_recorded else ""
    memory.type = memory.memory_type
    memory.people = ", ".join(memory.get_people()) if memory.get_people() else ""
    memory.feeling = memory.reflection
    memory.photo_urls_list = memory.get_photos()
    return render_template("edit_memory.html", memory=memory, tags=tags)


@memories_bp.route("/people")
def people_page():
    """人物档案列表"""
    people = People.query.order_by(People.name).all()
    return render_template("tags.html", tags=people, page_mode="people")


@memories_bp.route("/people/<int:pid>")
def person_detail_page(pid):
    """人物详情"""
    person = People.query.get(pid)
    if not person:
        return "人物不存在", 404
    memories = (
        Memory.query.filter(Memory.people_involved.contains(person.name))
        .order_by(Memory.create_time.desc())
        .all()
    )
    return jsonify({
        "person": {
            "id": person.id,
            "name": person.name,
            "relation": person.relation,
            "bio": person.bio,
            "photo_url": person.photo_url,
        },
        "memories": [
            {"id": m.id, "title": m.title, "date": str(m.date_recorded) if m.date_recorded else ""}
            for m in memories
        ]
    })


@memories_bp.route("/tags")
def tags_page():
    tags = Tag.query.all()
    return render_template("tags.html", tags=tags)


@memories_bp.route("/backups")
def backups_page():
    backups = Backup.query.order_by(Backup.created_at.desc()).all()
    return render_template("backups.html", backups=backups)


# ═══ Timeline API ═══


@memories_bp.route("/api/memories/timeline")
def api_memories_timeline():
    memories = Memory.query.order_by(Memory.date_recorded.desc()).all()
    grouped = collections.OrderedDict()
    for m in memories:
        if m.date_recorded:
            year = m.date_recorded.year
            month = m.date_recorded.month
        elif m.create_time:
            year = m.create_time.year
            month = m.create_time.month
        else:
            year, month = 2024, 1
        if year not in grouped:
            grouped[year] = collections.OrderedDict()
        if month not in grouped[year]:
            grouped[year][month] = []
        grouped[year][month].append(
            {
                "id": m.id,
                "title": m.title,
                "date": str(m.date_recorded)
                if m.date_recorded
                else str(m.create_time.date())
                if m.create_time
                else "",
                "tags": [{"name": t} for t in m.get_tags()] if m.get_tags() else [],
            }
        )
    result = []
    for year in sorted(grouped.keys(), reverse=True):
        months_list = []
        for month in sorted(grouped[year].keys(), reverse=True):
            months_list.append({"month": month, "memories": grouped[year][month]})
        result.append({"year": year, "months": months_list})
    return jsonify({"memories": result})


# ═══ 记忆 CRUD API ═══


@memories_bp.route("/api/memories", methods=["GET", "POST"])
def api_memories():
    if request.method == "POST":
        if "user" not in session:
            return jsonify({"msg": "未登录"}), 401
        username = session["user"]
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({"msg": "用户不存在"}), 404
        data = request.json
        if not data.get("title") or not data.get("content"):
            return jsonify({"msg": "标题和内容不能为空"}), 400
        new_memory = Memory(
            title=data["title"],
            content=data.get("content", ""),
            reflection=data.get("feeling", ""),
            memory_type=data.get("type", "text"),
            date_recorded=_parse_date(data.get("date")) or date.today(),
            author_id=user.id,  # 设置作者ID
            people_involved="[]",
            tags=json.dumps(data.get("tag_ids", []))
            if isinstance(data.get("tag_ids"), list)
            else "[]",
            is_public=True,
        )
        people_str = data.get("people", "")
        if people_str:
            new_memory.people_involved = json.dumps(
                [p.strip() for p in people_str.split(",") if p.strip()]
            )
        photo_urls = data.get("photo_urls", [])
        if photo_urls:
            new_memory.photo_urls = json.dumps(photo_urls)
        video_urls = data.get("video_urls", [])
        if video_urls:
            new_memory.video_urls = json.dumps(video_urls)
        db.session.add(new_memory)
        db.session.commit()
        _sync_memory_tags(new_memory.id, data.get("tag_ids", []))
        return jsonify(
            {"msg": "记忆创建成功", "memory": _memory_to_dict(new_memory)}
        ), 201

    # GET - list
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    tag_filter = request.args.get("tag", "", type=str)
    search = request.args.get("search", "", type=str)
    query = Memory.query.order_by(Memory.create_time.desc())
    query = _filter_by_tag(query, tag_filter)
    if search:
        query = query.filter(
            db.or_(Memory.title.contains(search), Memory.content.contains(search))
        )
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify(
        {
            "data": [_memory_to_dict(m) for m in pagination.items],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": pagination.total,
                "pages": pagination.pages,
            },
        }
    )


@memories_bp.route("/api/memories/<int:mid>", methods=["GET", "PUT", "DELETE"])
def api_memory_detail(mid):
    memory = Memory.query.get_or_404(mid)
    if request.method == "GET":
        return jsonify(_memory_to_dict(memory))
    if "user" not in session:
        return jsonify({"msg": "未登录"}), 401
    if request.method == "PUT":
        data = request.json
        memory.title = data.get("title", memory.title)
        memory.content = data.get("content", memory.content)
        memory.reflection = data.get("feeling", memory.reflection)
        memory.memory_type = data.get("type", memory.memory_type)
        if data.get("date"):
            memory.date_recorded = _parse_date(data["date"])
        people_str = data.get("people", "")
        if people_str:
            memory.people_involved = json.dumps(
                [p.strip() for p in people_str.split(",") if p.strip()]
            )
        if "photo_urls" in data:
            memory.photo_urls = json.dumps(data["photo_urls"])
        if "video_urls" in data:
            memory.video_urls = json.dumps(data["video_urls"])
        if "tag_ids" in data:
            memory.tags = json.dumps(data["tag_ids"])
            _sync_memory_tags(memory.id, data["tag_ids"])
        memory.update_time = datetime.utcnow()
        db.session.commit()
        return jsonify({"msg": "记忆更新成功", "memory": _memory_to_dict(memory)})
    # DELETE
    if "user" not in session:
        return jsonify({"msg": "未登录"}), 401
    db.session.delete(memory)
    db.session.commit()
    return jsonify({"msg": "记忆已删除"})


@memories_bp.route("/api/memories/new", methods=["GET"])
def api_new_memory():
    tags = Tag.query.all()
    return jsonify(
        {"tags": [{"id": t.id, "name": t.name, "color": t.color} for t in tags]}
    )


# ═══ 媒体文件 API ═══

ALLOWED_IMAGE_EXTS = {"png", "jpg", "jpeg", "gif", "webp", "bmp"}
ALLOWED_VIDEO_EXTS = {"mp4", "webm", "mov", "avi"}
ALLOWED_EXTS = ALLOWED_IMAGE_EXTS | ALLOWED_VIDEO_EXTS
MAX_FILE_SIZE = 20 * 1024 * 1024


def _allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTS


@memories_bp.route("/api/media", methods=["GET", "POST"])
def api_media():
    if "user" not in session:
        return jsonify({"msg": "未登录"}), 401
    username = session["user"]
    user = User.query.filter_by(username=username).first()
    if not user or user.role not in ("user", "admin"):
        return jsonify({"msg": "无权限"}), 403
    pending = PendingUser.query.filter_by(username=username).first()
    if pending and pending.status != "approved":
        return jsonify({"msg": "请等待审核通过后使用此功能"}), 403

    if request.method == "POST":
        if "file" not in request.files:
            return jsonify({"msg": "没有文件"}), 400
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"msg": "没有选择文件"}), 400
        if not _allowed_file(file.filename):
            return jsonify(
                {"msg": "不支持的文件格式，仅支持: " + ", ".join(sorted(ALLOWED_EXTS))}
            ), 400
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)
        if file_size > MAX_FILE_SIZE:
            return jsonify(
                {"msg": f"文件大小不能超过 {MAX_FILE_SIZE // 1024 // 1024}MB"}
            ), 400
        import uuid
        from werkzeug.utils import secure_filename
        from flask import current_app

        ext = file.filename.rsplit(".", 1)[1].lower()
        unique_name = f"{uuid.uuid4().hex}.{ext}"
        file_type = "image" if ext in ALLOWED_IMAGE_EXTS else "video"
        upload_folder = os.path.join(
            current_app.config.get("UPLOAD_FOLDER", "uploads"), file_type + "s"
        )
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, unique_name)
        file.save(file_path)
        media = MediaFile(
            user_id=user.id,
            file_type=file_type,
            file_url=f"/uploads/{file_type}s/{unique_name}",
            file_size=file_size,
            original_name=file.filename,
            title=request.form.get("title", ""),
            description=request.form.get("description", ""),
            is_public=request.form.get("is_public", "true") == "true",
        )
        db.session.add(media)
        log = AuditLog(
            action="upload",
            target_type="media",
            detail=f"用户上传{file_type}文件: {file.filename}",
            ip_address=request.remote_addr,
        )
        db.session.add(log)
        db.session.commit()
        return jsonify(
            {
                "msg": "上传成功",
                "media": {
                    "id": media.id,
                    "file_url": media.file_url,
                    "file_type": media.file_type,
                    "file_size": media.file_size,
                },
            }
        ), 201

    # GET
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    media_type = request.args.get("type", "", type=str)
    query = MediaFile.query.order_by(MediaFile.created_at.desc())
    if media_type in ("image", "video"):
        query = query.filter_by(file_type=media_type)
    if user.role != "admin":
        query = query.filter(
            db.or_(MediaFile.is_public == True, MediaFile.user_id == user.id)
        )
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
                    "thumbnail_url": m.thumbnail_url,
                    "original_name": m.original_name,
                    "description": m.description,
                    "is_public": m.is_public,
                    "view_count": m.view_count,
                    "user_id": m.user_id,
                    "username": m.owner.username if m.owner else None,
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


@memories_bp.route("/api/media/<int:mid>", methods=["GET", "DELETE"])
def api_media_detail(mid):
    media = MediaFile.query.get_or_404(mid)
    if request.method == "GET":
        media.view_count += 1
        db.session.commit()
        return jsonify(
            {
                "id": media.id,
                "title": media.title,
                "file_url": media.file_url,
                "file_type": media.file_type,
                "file_size": media.file_size,
                "thumbnail_url": media.thumbnail_url,
                "original_name": media.original_name,
                "description": media.description,
                "is_public": media.is_public,
                "view_count": media.view_count,
                "user": media.owner.username if media.owner else None,
                "created_at": media.created_at.isoformat()
                if media.created_at
                else None,
            }
        )
    # DELETE
    if "user" not in session:
        return jsonify({"msg": "未登录"}), 401
    username = session["user"]
    user = User.query.filter_by(username=username).first()
    if media.user_id != user.id and user.role != "admin":
        return jsonify({"msg": "无权限"}), 403
    from flask import current_app

    # 修正路径：media.file_url 形如 "/uploads/images/xxx.png"，
    # 需去掉前缀 "/uploads/" 再拼到 UPLOAD_FOLDER，否则会变成 uploads/uploads/...
    rel = media.file_url
    if rel.startswith("/uploads/"):
        rel = rel[len("/uploads/"):]
    elif rel.startswith("/"):
        rel = rel[1:]
    file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], rel)
    if os.path.exists(file_path):
        os.remove(file_path)
    db.session.delete(media)
    db.session.commit()
    return jsonify({"msg": "删除成功"})


@memories_bp.route("/api/media/user")
def api_user_media():
    if "user" not in session:
        return jsonify({"msg": "未登录"}), 401
    username = session["user"]
    pending = PendingUser.query.filter_by(username=username).first()
    if pending and pending.status != "approved":
        return jsonify(
            {
                "data": [],
                "pagination": {"page": 1, "per_page": 20, "total": 0, "pages": 0},
            }
        )
    user = User.query.filter_by(username=username).first()
    media_list = (
        MediaFile.query.filter_by(user_id=user.id)
        .order_by(MediaFile.created_at.desc())
        .all()
    )
    return jsonify(
        {
            "data": [
                {
                    "id": m.id,
                    "title": m.title,
                    "file_url": m.file_url,
                    "file_type": m.file_type,
                    "file_size": m.file_size,
                    "thumbnail_url": m.thumbnail_url,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in media_list
            ],
            "pagination": {
                "page": 1,
                "per_page": len(media_list),
                "total": len(media_list),
                "pages": 1,
            },
        }
    )


# ═══ 通知 API ═══


@memories_bp.route("/api/notifications")
def api_notifications():
    if "user" not in session:
        return jsonify({"msg": "未登录"}), 401
    username = session["user"]
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"msg": "用户不存在"}), 404
    page = request.args.get("page", 1, type=int)
    per_page = 20
    query = Notification.query.filter_by(user_id=user.id).order_by(
        Notification.created_at.desc()
    )
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify(
        {
            "data": [
                {
                    "id": n.id,
                    "title": n.title,
                    "content": n.content,
                    "type": n.notification_type,
                    "is_read": n.is_read,
                    "created_at": n.created_at.isoformat() if n.created_at else None,
                }
                for n in pagination.items
            ],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": pagination.total,
                "pages": pagination.pages,
            },
        }
    )


@memories_bp.route("/api/notifications/<int:nid>/read", methods=["POST"])
def mark_notification_read(nid):
    if "user" not in session:
        return jsonify({"msg": "未登录"}), 401
    notif = Notification.query.get(nid)
    if not notif:
        return jsonify({"msg": "通知不存在"}), 404
    notif.is_read = True
    db.session.commit()
    return jsonify({"msg": "已标记"})


@memories_bp.route("/api/notifications/read-all", methods=["POST"])
def mark_all_notifications_read():
    if "user" not in session:
        return jsonify({"msg": "未登录"}), 401
    username = session["user"]
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"msg": "用户不存在"}), 404
    Notification.query.filter_by(user_id=user.id, is_read=False).update(
        {"is_read": True}
    )
    db.session.commit()
    return jsonify({"msg": "已全部标记"})


@memories_bp.route("/api/notifications/unread-count")
def api_unread_count():
    if "user" not in session:
        return jsonify({"count": 0})
    username = session["user"]
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"count": 0})
    count = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    return jsonify({"count": count})
