"""数据库配置"""
import os

class DatabaseConfig:
    """数据库配置"""
    # MySQL 数据库配置
    # 注意：Windows上MySQL服务名通常是MySQL80，但连接时使用localhost:3306
    # 数据库名和表名在Windows不区分大小写，Linux区分大小写，建议统一小写
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')  # 数据库主机地址
    MYSQL_PORT = os.getenv('MYSQL_PORT', '3306')  # 数据库端口（默认3306）
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')  # 数据库用户名
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'y1017285149')  # 数据库密码
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'stroke_prediction')  # 数据库名称（建议小写）
    
    # 数据库连接URI（使用pymysql驱动）
    DATABASE_URI = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4'
    
    # 数据库表名（统一小写，避免跨平台问题）
    PREDICTION_TABLE = 'predictions'
    
    # 连接池配置
    ECHO = False  # 是否打印SQL语句（调试用）
    POOL_SIZE = 10  # 连接池大小
    MAX_OVERFLOW = 20  # 最大溢出连接数
    POOL_RECYCLE = 3600  # 连接回收时间（秒）
