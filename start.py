"""
智能启动脚本

自动检查数据库状态，如果需要修复则先修复，然后启动应用
"""

import sys
import os
import subprocess
import pymysql
from config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB, MYSQL_PORT

def check_database_ready():
    """检查数据库是否准备就绪"""
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
            
            for table in required_tables:
                cursor.execute(f"SHOW TABLES LIKE '{table}'")
                if not cursor.fetchone():
                    print(f"❌ 表 '{table}' 不存在")
                    return False
            
            # 检查news表的category_id列
            cursor.execute("DESCRIBE news")
            columns = cursor.fetchall()
            column_names = [col['Field'] for col in columns]
            
            if 'category_id' not in column_names:
                print("❌ news表缺少category_id列")
                return False
            
            # 检查是否有基本数据
            cursor.execute("SELECT COUNT(*) as count FROM categories")
            if cursor.fetchone()['count'] == 0:
                print("❌ categories表没有数据")
                return False
        
        connection.close()
        print("✅ 数据库状态正常")
        return True
        
    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")
        return False

def run_fix():
    """运行修复脚本"""
    print("🔧 运行数据库修复...")
    try:
        result = subprocess.run([sys.executable, 'one_click_fix.py'], 
                              capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print("✅ 修复成功")
            return True
        else:
            print("❌ 修复失败:")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ 修复过程异常: {e}")
        return False

def start_app():
    """启动应用"""
    print("🚀 启动乡村信息平台...")
    try:
        # 直接运行app.py
        os.system(f"{sys.executable} app.py")
    except KeyboardInterrupt:
        print("\n👋 应用已停止")
    except Exception as e:
        print(f"❌ 应用启动失败: {e}")

def main():
    """主函数"""
    print("🌟 乡村信息平台智能启动器")
    print("=" * 50)
    
    # 检查数据库状态
    if not check_database_ready():
        print("\n数据库需要修复，正在自动修复...")
        if not run_fix():
            print("❌ 自动修复失败，请手动运行: python one_click_fix.py")
            return False
        
        # 再次检查
        if not check_database_ready():
            print("❌ 修复后数据库仍有问题")
            return False
    
    # 启动应用
    print("\n数据库状态正常，启动应用...")
    start_app()
    
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断启动过程")
    except Exception as e:
        print(f"\n❌ 启动器异常: {e}")
    finally:
        input("\n按回车键退出...")
        sys.exit(0)