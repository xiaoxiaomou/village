"""
测试数据库连接
"""

import pymysql
from config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB, MYSQL_PORT

def test_connection():
    """测试数据库连接"""
    print("🔍 测试数据库连接...")
    print(f"主机: {MYSQL_HOST}")
    print(f"端口: {MYSQL_PORT}")
    print(f"用户: {MYSQL_USER}")
    print(f"数据库: {MYSQL_DB}")
    
    try:
        # 先尝试连接到MySQL服务器（不指定数据库）
        print("\n1. 测试MySQL服务器连接...")
        connection = pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            port=int(MYSQL_PORT)
        )
        print("✅ MySQL服务器连接成功")
        
        # 检查数据库是否存在
        with connection.cursor() as cursor:
            cursor.execute("SHOW DATABASES")
            databases = [db[0] for db in cursor.fetchall()]
            print(f"可用数据库: {', '.join(databases)}")
            
            if MYSQL_DB in databases:
                print(f"✅ 数据库 '{MYSQL_DB}' 存在")
            else:
                print(f"❌ 数据库 '{MYSQL_DB}' 不存在")
                print("正在创建数据库...")
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DB} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                print(f"✅ 数据库 '{MYSQL_DB}' 创建成功")
        
        connection.close()
        
        # 再次尝试连接到指定数据库
        print(f"\n2. 测试连接到数据库 '{MYSQL_DB}'...")
        connection = pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
            port=int(MYSQL_PORT)
        )
        print("✅ 数据库连接成功")
        
        # 检查表
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = [table[0] for table in cursor.fetchall()]
            if tables:
                print(f"现有表: {', '.join(tables)}")
            else:
                print("数据库中没有表")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False

if __name__ == "__main__":
    test_connection()