"""
乡村记忆系统 - 应用入口
"""

import os
import sys


# 修复 Windows + Python 3.11 + SQLAlchemy 兼容性
def _bootstrap_asyncio_stub():
    if not sys.platform.startswith("win"):
        return
    if "asyncio" in sys.modules and hasattr(sys.modules["asyncio"], "BaseEventLoop"):
        return
    try:
        import asyncio  # noqa: F401

        return
    except OSError:
        pass
    import types

    stub = types.ModuleType("asyncio")
    for _n in (
        "iscoroutine",
        "iscoroutinefunction",
        "Future",
        "ensure_future",
        "get_event_loop",
        "new_event_loop",
        "set_event_loop",
        "run",
        "wait",
        "gather",
        "create_task",
        "sleep",
        "AbstractEventLoop",
        "BaseEventLoop",
        "coroutine",
        "Task",
        "Lock",
        "Event",
        "Queue",
        "Runner",
        "get_running_loop",
        "_set_running_loop",
    ):
        setattr(stub, _n, None)

    class _Exc(Exception):
        pass

    for _n in (
        "TimeoutError",
        "CancelledError",
        "InvalidStateError",
        "IncompleteReadError",
        "LimitOverrunError",
        "SendfileNotAvailableError",
        "StaggeredException",
    ):
        setattr(stub, _n, _Exc)
    sys.modules["asyncio"] = stub
    for _m in (
        "asyncio.windows_events",
        "asyncio.windows_utils",
        "asyncio.selector_events",
        "asyncio.proactor_events",
        "asyncio.base_events",
        "asyncio.events",
        "asyncio.coroutines",
    ):
        sys.modules.setdefault(_m, types.ModuleType(_m))


_bootstrap_asyncio_stub()

from routes import create_app

app = create_app()

if __name__ == "__main__":
    from werkzeug.security import generate_password_hash
    from models import db, User

    with app.app_context():
        db.create_all()
        admin = User.query.filter_by(username="admin").first()
        if not admin:
            admin = User(
                username="admin",
                password_hash=generate_password_hash("admin123"),
                role="admin",
            )
            db.session.add(admin)
            db.session.commit()

    app.run(host="0.0.0.0", port=5000, debug=False)
