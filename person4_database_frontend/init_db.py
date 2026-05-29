"""MySQL数据库初始化脚本"""
import pymysql
from database.config import DatabaseConfig


def drop_database():
    """删除数据库（如果存在）"""
    try:
        # 连接到 MySQL 服务器（不指定数据库）
        connection = pymysql.connect(
            host=DatabaseConfig.MYSQL_HOST,
            port=int(DatabaseConfig.MYSQL_PORT),
            user=DatabaseConfig.MYSQL_USER,
            password=DatabaseConfig.MYSQL_PASSWORD,
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # 删除数据库
        cursor.execute(f"DROP DATABASE IF EXISTS `{DatabaseConfig.MYSQL_DATABASE}`")
        
        print(f"✓ 数据库 '{DatabaseConfig.MYSQL_DATABASE}' 已删除")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"✗ 删除数据库失败: {str(e)}")
        return False


def create_database():
    """创建数据库（如果不存在）"""
    try:
        # 连接到 MySQL 服务器（不指定数据库）
        connection = pymysql.connect(
            host=DatabaseConfig.MYSQL_HOST,
            port=int(DatabaseConfig.MYSQL_PORT),
            user=DatabaseConfig.MYSQL_USER,
            password=DatabaseConfig.MYSQL_PASSWORD,
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # 创建数据库
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{DatabaseConfig.MYSQL_DATABASE}` "
            f"DEFAULT CHARACTER SET utf8mb4 "
            f"DEFAULT COLLATE utf8mb4_unicode_ci"
        )
        
        print(f"✓ 数据库 '{DatabaseConfig.MYSQL_DATABASE}' 创建成功或已存在")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f" 创建数据库失败: {str(e)}")
        print("\n请检查：")
        print("1. MySQL 服务是否已启动")
        print("2. 用户名和密码是否正确")
        print("3. MySQL 是否允许远程连接（如果不是localhost）")
        return False


def test_connection():
    """测试数据库连接"""
    try:
        connection = pymysql.connect(
            host=DatabaseConfig.MYSQL_HOST,
            port=int(DatabaseConfig.MYSQL_PORT),
            user=DatabaseConfig.MYSQL_USER,
            password=DatabaseConfig.MYSQL_PASSWORD,
            database=DatabaseConfig.MYSQL_DATABASE,
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        
        print(f"✓ MySQL 连接成功！")
        print(f"  MySQL 版本: {version[0]}")
        print(f"  数据库: {DatabaseConfig.MYSQL_DATABASE}")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f" MySQL 连接失败: {str(e)}")
        return False


if __name__ == '__main__':
    print("=" * 50)
    print("MySQL 数据库初始化")
    print("=" * 50)
    print()
    
    # 询问用户是否删除原有数据库
    print("⚠️  警告：此操作将删除原有数据库并重建！")
    confirm = input("是否继续？(yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("✗ 操作已取消")
        exit(0)
    
    print()
    print("1. 删除原有数据库...")
    if drop_database():
        print()
        print("2. 创建新数据库...")
        if create_database():
            print()
            print("3. 测试数据库连接...")
            if test_connection():
                print()
                print("4. 创建数据表...")
                from database.db import init_db
                init_db()
                print()
                print("✓ 数据库初始化完成！")
            else:
                print()
                print("✗ 数据库连接失败，请检查配置。")
        else:
            print()
            print("✗ 数据库创建失败，请检查 MySQL 配置。")
    else:
        print()
        print("✗ 数据库删除失败，请检查 MySQL 配置。")
        print("修改 database/config.py 中的配置：")
        print("  - MYSQL_HOST")
        print("  - MYSQL_PORT")
        print("  - MYSQL_USER")
        print("  - MYSQL_PASSWORD")
        print("  - MYSQL_DATABASE")
