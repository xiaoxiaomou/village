# -*- coding: utf-8 -*-
"""
SQLite 数据库连接测试
原 MySQL 版本已重写以匹配项目当前使用的 SQLite 配置
"""
import os
import sys
import sqlite3

# 确保可以导入项目根目录
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from config import DATABASE


def test_connection():
    """测试 SQLite 数据库连接"""
    print("测试 SQLite 数据库连接...")
    print(f"数据库路径: {DATABASE}")

    if not os.path.exists(DATABASE):
        print(f"数据库文件不存在: {DATABASE}")
        print("请先运行: python db_tools.py init")
        return False

    conn = None
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 简单查询
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1, "简单查询失败"
        print("数据库连接成功")

        # 列出所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"表数量: {len(tables)}")
        for t in tables:
            print(f"  - {t}")

        # 统计每张表行数
        print("表记录数:")
        for t in tables:
            try:
                cursor.execute(f'SELECT COUNT(*) FROM "{t}"')
                count = cursor.fetchone()[0]
                print(f"    {t}: {count} 条")
            except sqlite3.Error as e:
                print(f"    {t}: 查询失败 ({e})")

        return True
    except sqlite3.Error as e:
        print(f"连接失败: {e}")
        return False
    except AssertionError as e:
        print(f"断言失败: {e}")
        return False
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    ok = test_connection()
    sys.exit(0 if ok else 1)
