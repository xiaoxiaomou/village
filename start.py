# -*- coding: utf-8 -*-
"""
乡村记忆系统 - 智能启动脚本
自动检测环境、创建目录、初始化数据库、启动服务
"""
import os
import sys
import subprocess

def _bootstrap_asyncio_stub():
    if not sys.platform.startswith('win'):
        return
    if 'asyncio' in sys.modules:
        return
    import types
    stub = types.ModuleType('asyncio')
    
    def _iscoroutine(obj):
        return False
    
    def _iscoroutinefunction(obj):
        return False
    
    setattr(stub, 'iscoroutine', _iscoroutine)
    setattr(stub, 'iscoroutinefunction', _iscoroutinefunction)
    
    for _n in (
        'Future', 'ensure_future', 'get_event_loop', 'new_event_loop',
        'set_event_loop', 'run', 'wait', 'gather', 'create_task', 'sleep',
        'AbstractEventLoop', 'BaseEventLoop', 'coroutine', 'Task', 'Lock',
        'Event', 'Queue', 'Runner', 'get_running_loop', '_set_running_loop',
        'all_tasks', 'current_task', 'as_completed', 'shield', 'timeout',
        'to_thread', 'start_server', 'open_connection', 'Semaphore',
        'Condition', 'Barrier', 'BoundedSemaphore', 'Timer', 'create_subprocess_exec',
        'create_subprocess_shell', 'Pipe', 'StreamReader', 'StreamWriter',
        'IncompleteReadError', 'LimitOverrunError', 'TimeoutError', 'CancelledError',
        'InvalidStateError', 'SendfileNotAvailableError', 'StaggeredException',
        'Protocol', 'Transport', 'DatagramProtocol', 'BaseProtocol',
        'SubprocessProtocol', 'BufferedProtocol', 'FlowControlMixin',
        'AbstractServer', 'Server', 'DatagramServer', 'BaseTransport',
        'ReadTransport', 'WriteTransport', 'ReadWriteTransport',
        'Transport', 'Protocol', 'BufferedWriter', 'BufferedReader',
        'StreamReaderProtocol', 'StreamWriter', 'ProactorEventLoop',
        'SelectorEventLoop', 'DefaultEventLoopPolicy', 'WindowsSelectorEventLoopPolicy',
        'WindowsProactorEventLoopPolicy', 'UnixSelectorEventLoopPolicy',
    ):
        setattr(stub, _n, None)
    
    stub.__path__ = []
    stub.__package__ = 'asyncio'
    
    def _getattr(name):
        return None
    
    stub.__getattr__ = _getattr
    
    sys.modules['asyncio'] = stub
    print('  [兼容] 已启用 asyncio stub (Windows + SQLAlchemy 兼容层)')

_bootstrap_asyncio_stub()

APP_PORT = int(os.environ.get('PORT', 5000))
APP_HOST = os.environ.get('HOST', '0.0.0.0')
DEBUG_MODE = os.environ.get('FLASK_DEBUG', '0') == '1'
VILLAGE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(VILLAGE_DIR, 'uploads')
BACKUP_DIR = os.path.join(VILLAGE_DIR, 'backups')


def print_banner():
    print("\n" + "=" * 50)
    print("  乡村记忆系统 v2.0 (SQLite)")
    print("=" * 50 + "\n")


def ensure_directories():
    for d in [UPLOAD_DIR, BACKUP_DIR]:
        os.makedirs(d, exist_ok=True)
        print(f"  目录就绪: {d}")


def check_dependencies():
    required = ['flask', 'flask_cors', 'flask_login']
    missing = []
    for pkg in required:
        try:
            __import__(pkg.replace('-', '_'))
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"  安装依赖: {', '.join(missing)}")
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '-r',
            os.path.join(VILLAGE_DIR, 'requirements.txt')
        ])
        print("  依赖安装完成")
    else:
        print("  依赖检查通过")


def init_database():
    print("  初始化数据库...")
    from db_tools import init_database as init_db, init_default_data
    init_db()
    init_default_data()
    print("  数据库初始化完成")


def start_server():
    print_banner()
    ensure_directories()
    check_dependencies()
    init_database()
    print(f"  访问地址: http://localhost:{APP_PORT}")
    print(f"  调试模式: {'开启' if DEBUG_MODE else '关闭'}")
    print(f"  数据库:   village.db (SQLite)")
    print(f"  上传目录: {UPLOAD_DIR}")
    print(f"  备份目录: {BACKUP_DIR}")
    print()
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from app import app
    application = app
    try:
        application.run(host=APP_HOST, port=APP_PORT, debug=DEBUG_MODE, threaded=False)
    except KeyboardInterrupt:
        print("\n  服务已停止")


def install_deps():
    print("  安装依赖...")
    req = os.path.join(VILLAGE_DIR, 'requirements.txt')
    if os.path.exists(req):
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', req])
        print("  完成")
    else:
        print("  requirements.txt 不存在")


def init_db_only():
    from db_tools import init_database as init_db, init_default_data
    init_db()
    init_default_data()
    print("  数据库初始化完成")


def show_info():
    print("  系统信息")
    print(f"  Python: {sys.version}")
    print(f"  目录:   {VILLAGE_DIR}")
    print(f"  端口:   {APP_PORT}")
    print(f"  调试:   {'开启' if DEBUG_MODE else '关闭'}")
    db_path = os.path.join(VILLAGE_DIR, 'village.db')
    print(f"  数据库: {'存在' if os.path.exists(db_path) else '不存在'}")
    print(f"  uploads/: {'存在' if os.path.exists(UPLOAD_DIR) else '不存在'}")
    print(f"  backups/: {'存在' if os.path.exists(BACKUP_DIR) else '不存在'}")


if __name__ == '__main__':
    action = sys.argv[1] if len(sys.argv) > 1 else 'start'
    actions = {
        'start': start_server,
        'run': start_server,
        'install': install_deps,
        'init-db': init_db_only,
        'info': show_info,
        'help': lambda: print(__doc__ or '用法: python start.py [start|install|init-db|info|help]'),
    }
    handler = actions.get(action)
    if handler:
        handler()
    else:
        print(f"  未知命令: {action}")
        show_info()
        sys.exit(1)
