"""
认证蓝图：登录、注册、注销、用户中心
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
from werkzeug.security import generate_password_hash
from models import db, User, PendingUser, Notification, AuditLog
from datetime import datetime

auth_bp = Blueprint("auth", __name__)


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


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    if not username or not password:
        flash("请填写用户名和密码")
        return redirect(url_for("auth.login"))

    # Try active user
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        session["user"] = username
        session["role"] = user.role
        if user.role == "admin":
            return redirect(url_for("admin.admin_dashboard"))
        else:
            return redirect(url_for("main.index"))

    # Try pending user
    pending = PendingUser.query.filter_by(username=username).first()
    if pending and pending.check_password(password):
        if pending.status == "approved":
            session["user"] = username
            session["role"] = "user"
            return redirect(url_for("main.index"))
        elif pending.status == "rejected":
            flash("您的注册申请已被拒绝: " + (pending.review_comment or "未说明原因"))
            return redirect(url_for("auth.login"))
        else:
            flash("您的注册申请还在审核中，请耐心等待")
            return redirect(url_for("auth.login"))

    flash("用户名或密码错误")
    return redirect(url_for("auth.login"))


@auth_bp.route("/logout")
def logout():
    """用户注销"""
    session.pop("user", None)
    session.pop("role", None)
    flash("已成功退出登录")
    return redirect(url_for("main.index"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    nickname = request.form.get("nickname", "").strip()
    password = request.form.get("password")
    confirm_password = request.form.get("confirm_password")

    if not username or not password or not confirm_password:
        flash("请填写用户名和密码")
        return redirect(url_for("auth.register"))
    if len(username) < 3:
        flash("用户名至少3个字符")
        return redirect(url_for("auth.register"))
    if not email or "@" not in email:
        flash("请输入有效邮箱")
        return redirect(url_for("auth.register"))
    if password != confirm_password:
        flash("两次密码输入不一致")
        return redirect(url_for("auth.register"))
    if len(password) < 6:
        flash("密码至少6个字符")
        return redirect(url_for("auth.register"))

    # Check existing
    existing = db.session.execute(
        db.text("SELECT id FROM users WHERE username=:u OR email=:e"),
        params={"u": username, "e": email},
    ).fetchone()
    if existing:
        flash("用户名或邮箱已存在")
        return redirect(url_for("auth.register"))

    pending = PendingUser.query.filter(
        (PendingUser.username == username) | (PendingUser.email == email)
    ).first()
    if pending:
        flash("该用户名或邮箱已有待审核申请，请等待审核")
        return redirect(url_for("auth.register"))

    new_pending = PendingUser(
        username=username,
        email=email,
        phone=phone if phone else None,
        nickname=nickname if nickname else username,
    )
    new_pending.set_password(password)
    new_pending.status = "pending"

    try:
        db.session.add(new_pending)
        admins = User.query.filter_by(role="admin").all()
        for admin in admins:
            notify = Notification(
                user_id=admin.id,
                title="新用户注册申请",
                content=f'用户 "{username}" ({email}) 已提交注册申请，请审核',
                notification_type="info",
                is_read=False,
            )
            db.session.add(notify)
        log = AuditLog(
            action="register",
            target_type="user",
            detail=f'用户 "{username}" 提交注册申请',
            ip_address=request.remote_addr,
        )
        db.session.add(log)
        db.session.commit()
        flash("注册申请已提交，请等待管理员审核通过")
        return redirect(url_for("auth.login"))
    except Exception as e:
        db.session.rollback()
        flash(f"注册失败: {str(e)}")
        return redirect(url_for("auth.register"))


@auth_bp.route("/dashboard")
def user_dashboard():
    """用户中心"""
    if "user" not in session:
        return redirect(url_for("auth.login"))
    username = session["user"]
    user = User.query.filter_by(username=username).first()
    if not user:
        return redirect(url_for("auth.login"))
    pending = PendingUser.query.filter_by(username=username).first()
    return render_template("user_dashboard.html", user=user, pending=pending)


@auth_bp.route("/api/pending-status")
@auth_bp.route("/api/users/pending-status")
def api_pending_status():
    """获取当前用户的注册审核状态"""
    if "user" not in session:
        return jsonify({"msg": "未登录"}), 401
    username = session["user"]
    pending = PendingUser.query.filter_by(username=username).first()
    if pending:
        return jsonify(
            {
                "status": pending.status,
                "username": pending.username,
                "review_comment": pending.review_comment
                if pending.status == "rejected"
                else None,
            }
        )
    return jsonify({"status": "active"})


@auth_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "GET":
        return redirect(url_for("auth.login"))
    data = request.json
    username = data.get("username")
    password = data.get("password")
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password) and user.role == "admin":
        session["user"] = username
        session["role"] = "admin"
        return jsonify({"msg": "登录成功", "role": "admin"})
    return jsonify({"msg": "用户名或密码错误"}), 401


@auth_bp.route("/admin/logout", methods=["GET", "POST"])
def admin_logout():
    session.pop("user", None)
    session.pop("role", None)
    return jsonify({"msg": "已退出登录"})
