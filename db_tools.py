"""
数据库工具脚本

集成了数据库检查、修复和初始化功能
"""

import os
import sys
import pymysql
import importlib.util
from config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB, MYSQL_PORT

def check_config():
    """检查MySQL配置"""
    print("🔍 检查MySQL配置...")
    
    try:
        # 尝试连接数据库
        connection = pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
            port=int(MYSQL_PORT),
            cursorclass=pymysql.cursors.DictCursor
        )
        connection.close()
        print("✅ MySQL连接成功")
        return True
    except Exception as e:
        print(f"❌ MySQL连接失败: {e}")
        return False

def check_database_structure():
    """检查数据库结构"""
    print("🔍 检查数据库结构...")
    
    try:
        connection = pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
            port=int(MYSQL_PORT),
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection.cursor() as cursor:
            # 检查必要的表是否存在
            required_tables = ['users', 'categories', 'news', 'services', 'government', 'village_info', 'messages']
            missing_tables = []
            
            for table in required_tables:
                cursor.execute(f"SHOW TABLES LIKE '{table}'")
                if not cursor.fetchone():
                    missing_tables.append(table)
            
            if missing_tables:
                print(f"❌ 缺少表: {', '.join(missing_tables)}")
                return False
            
            # 检查news表的category_id列
            cursor.execute("DESCRIBE news")
            columns = cursor.fetchall()
            column_names = [col['Field'] for col in columns]
            
            if 'category_id' not in column_names:
                print("❌ news表缺少category_id列")
                return False
            
            if 'create_time' not in column_names:
                print("❌ news表缺少create_time列")
                return False
            
            # 检查是否有基本数据
            cursor.execute("SELECT COUNT(*) as count FROM categories")
            if cursor.fetchone()['count'] == 0:
                print("❌ categories表没有数据")
                return False
        
        connection.close()
        print("✅ 数据库结构检查通过")
        return True
    except Exception as e:
        print(f"❌ 数据库结构检查失败: {e}")
        return False

def fix_database_structure():
    """修复数据库结构"""
    print("🔧 修复数据库结构...")
    
    try:
        connection = pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
            port=int(MYSQL_PORT),
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection.cursor() as cursor:
            # 创建用户表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                email VARCHAR(100),
                phone VARCHAR(20),
                role ENUM('admin', 'user') DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # 创建分类表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # 创建新闻表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS news (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                content TEXT NOT NULL,
                category_id INT,
                image_url VARCHAR(255),
                create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
            """)
            
            # 创建服务表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS services (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                description TEXT NOT NULL,
                icon VARCHAR(50),
                link VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # 创建政务表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS government (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                content TEXT NOT NULL,
                publish_date DATE,
                department VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # 创建村情表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS village_info (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                content TEXT NOT NULL,
                type ENUM('history', 'culture', 'economy', 'education', 'other') DEFAULT 'other',
                image_url VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # 创建留言表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(50) NOT NULL,
                contact VARCHAR(100),
                content TEXT NOT NULL,
                reply TEXT,
                status ENUM('pending', 'replied', 'rejected') DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                replied_at TIMESTAMP NULL
            )
            """)
            
            # 检查news表是否有create_time列
            cursor.execute("DESCRIBE news")
            columns = cursor.fetchall()
            column_names = [col['Field'] for col in columns]
            
            if 'create_time' not in column_names:
                print("📝 添加create_time列...")
                cursor.execute("ALTER TABLE news ADD COLUMN create_time DATETIME DEFAULT CURRENT_TIMESTAMP")
                
                # 如果有其他时间列，用它们填充create_time
                if 'date' in column_names:
                    cursor.execute("UPDATE news SET create_time = CONCAT(date, ' 00:00:00') WHERE date IS NOT NULL")
                elif 'created_at' in column_names:
                    cursor.execute("UPDATE news SET create_time = created_at WHERE created_at IS NOT NULL")
            
            # 检查是否有默认分类
            cursor.execute("SELECT COUNT(*) as count FROM categories")
            if cursor.fetchone()['count'] == 0:
                print("📝 添加默认分类...")
                cursor.execute("""
                INSERT INTO categories (name, description) VALUES 
                ('村务公开', '村务公开相关信息'),
                ('通知公告', '村内通知和公告'),
                ('政策法规', '相关政策和法规解读'),
                ('乡村新闻', '乡村新闻动态')
                """)
            
            # 检查是否有管理员账户
            cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'admin'")
            if cursor.fetchone()['count'] == 0:
                print("📝 添加默认管理员账户...")
                # 默认密码: admin123
                cursor.execute("""
                INSERT INTO users (username, password, role) VALUES 
                ('admin', 'pbkdf2:sha256:150000$KJrEVcAx$b2c36b1999f8b99e7c7ac23cc4ac53f9c0d0d10b328bd9b8120bf7bcab47cdc6', 'admin')
                """)
        
        connection.commit()
        connection.close()
        print("✅ 数据库结构修复完成")
        return True
    except Exception as e:
        print(f"❌ 数据库结构修复失败: {e}")
        return False

def initialize_database():
    """初始化数据库"""
    print("🚀 初始化数据库...")
    
    if not check_config():
        print("❌ 配置检查失败，无法初始化数据库")
        return False
    
    if not check_database_structure():
        print("⚠️ 数据库结构检查失败，尝试修复...")
        if not fix_database_structure():
            print("❌ 数据库结构修复失败，无法初始化数据库")
            return False
    
    print("✅ 数据库初始化完成")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "check":
            check_config() and check_database_structure()
        elif command == "fix":
            fix_database_structure()
        elif command == "init":
            initialize_database()
        else:
            print(f"未知命令: {command}")
            print("可用命令: check, fix, init")
    else:
        initialize_database()