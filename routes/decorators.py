"""
统一权限装饰器：login_required / admin_required。

行为与原 auth.py / api.py / memories.py / admin.py 中定义完全一致：
- 未登录：``return jsonify({"msg": "未登录"}), 401``
- 已登录但非 admin：``jsonify({"msg": "无权限"}), 403``
"""

from functools import wraps

from flask import jsonify, session


def login_required(f):
    """要求已登录，否则返回 401 JSON。"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return jsonify({"msg": "未登录"}), 401
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """要求已登录且角色为 admin，否则返回 401 / 403 JSON。"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return jsonify({"msg": "未登录"}), 401
        if session.get("role") != "admin":
            return jsonify({"msg": "无权限"}), 403
        return f(*args, **kwargs)

    return decorated_function
