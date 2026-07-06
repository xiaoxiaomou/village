# 本地SQLite数据库配置
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
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
