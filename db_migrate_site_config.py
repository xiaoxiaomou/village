"""
SiteConfig 迁移脚本（T4）：为已存在的 village.db 追加 7 个新列并回填默认值。

背景：
    项目使用 SQLite，``app.py`` 仅 ``db.create_all()``，不会为已存在的
    ``site_config`` 表新增列。若模型已加列但未执行迁移，``SiteConfig.get()``
    的 SELECT 会因缺列报错 -> ``site_config=None`` -> 全站配置丢失。

幂等保证：
    1. 每条 ALTER 先用 ``PRAGMA table_info`` 检查列是否存在，避免重复 ALTER 报错；
    2. 回填仅对为 NULL/空的列写入 ``SiteConfig.default_values()`` 对应默认值，
       已有值的列不受影响；可重复运行，安全无副作用。

用法：
    C:/Users/xiao/.workbuddy/binaries/python/envs/default/Scripts/python.exe db_migrate_site_config.py
"""

import os
import sqlite3

from routes import create_app
from models import db, SiteConfig

# 7 个新增列（与 models.py SiteConfig 定义、default_values 双写一致）
NEW_COLUMNS = [
    "hero_subtitle",
    "stat_labels",
    "intro_title",
    "intro_subtitle",
    "features_title",
    "features_subtitle",
    "village_info_title",
]

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "village.db")


def _get_existing_columns(conn):
    """返回 site_config 表当前已有的列名集合。"""
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(site_config)")
    return {row[1] for row in cur.fetchall()}


def migrate():
    """对 site_config 执行幂等 ALTER ADD COLUMN。"""
    if not os.path.exists(DB_PATH):
        print(f"[跳过] 数据库文件不存在: {DB_PATH}")
        return
    conn = sqlite3.connect(DB_PATH)
    try:
        existing = _get_existing_columns(conn)
        added = []
        for col in NEW_COLUMNS:
            if col not in existing:
                conn.execute(f"ALTER TABLE site_config ADD COLUMN {col} TEXT")
                added.append(col)
        conn.commit()
        if added:
            print(f"[迁移] 已新增列: {added}")
        else:
            print("[迁移] 7 个新列均已存在，无需 ALTER")
    finally:
        conn.close()


def backfill():
    """用 SiteConfig.default_values() 回填为 NULL/空的新列（幂等）。"""
    app = create_app()
    with app.app_context():
        # 确保表与列存在（对已迁移的旧库为 no-op，对新库创建带新列的表）
        db.create_all()
        cfg = SiteConfig.query.first()
        if cfg is None:
            print("[回填] site_config 暂无数据行，首次启动将由种子流程填充，跳过回填")
            return
        defaults = SiteConfig.default_values()
        changed = False
        for col in NEW_COLUMNS:
            current = getattr(cfg, col, None)
            if current is None or current == "":
                setattr(cfg, col, defaults.get(col, ""))
                changed = True
        if changed:
            db.session.commit()
            print("[回填] 已用默认值补全为空的新列")
        else:
            print("[回填] 新列均有值，无需补全")


if __name__ == "__main__":
    migrate()
    backfill()
    print("[完成] SiteConfig 迁移与回填结束")
