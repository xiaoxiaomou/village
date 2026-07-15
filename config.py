# 本地SQLite数据库配置
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# 加载 .env（开发环境用，不进版本库）
_env_path = os.path.join(BASE_DIR, '.env')
if os.path.exists(_env_path):
    with open(_env_path, encoding='utf-8') as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith('#') and '=' in _line:
                _k, _v = _line.split('=', 1)
                os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))

DATABASE = os.path.join(BASE_DIR, 'village.db')

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + DATABASE
SQLALCHEMY_TRACK_MODIFICATIONS = False

SECRET_KEY = os.environ.get('SECRET_KEY', 'village-memory-secret-key-change-in-production')

# 上传文件夹
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
# 备份文件夹
BACKUP_FOLDER = os.path.join(BASE_DIR, 'backups')

# 每页显示条数
PAGE_SIZE = 20

# TinyMCE 富文本编辑器 API Key（从环境变量读取，避免密钥入库）
TINYMCE_API_KEY = os.environ.get('TINYMCE_API_KEY', 'no-api-key')
