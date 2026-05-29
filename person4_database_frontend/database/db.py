"""数据库连接模块"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
from database.config import DatabaseConfig
import pymysql

# 创建引擎
engine = create_engine(
    DatabaseConfig.DATABASE_URI,
    echo=DatabaseConfig.ECHO,
    pool_size=DatabaseConfig.POOL_SIZE,
    max_overflow=DatabaseConfig.MAX_OVERFLOW,
    pool_recycle=DatabaseConfig.POOL_RECYCLE,
    pool_pre_ping=True  # 连接前ping测试
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库（创建所有表）"""
    # 先检查数据库是否存在
    try:
        # 导入所有模型以确保它们被注册
        from database import models
        
        Base.metadata.create_all(bind=engine)
        print("✓ MySQL数据库初始化成功！")
        print(f"  数据库地址: {DatabaseConfig.MYSQL_HOST}:{DatabaseConfig.MYSQL_PORT}")
        print(f"  数据库名: {DatabaseConfig.MYSQL_DATABASE}")
    except Exception as e:
        print(f"✗ 数据库初始化失败: {str(e)}")
        raise


def close_db():
    """关闭数据库连接"""
    engine.dispose()
    print("✓ MySQL数据库连接已关闭")
