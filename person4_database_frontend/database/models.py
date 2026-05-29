"""数据库模型定义"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.sql import func
from database.db import Base


class PredictionRecord(Base):
    """预测记录表"""
    __tablename__ = 'predictions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 患者基本信息
    gender = Column(String(20), nullable=False)  # 性别
    age = Column(Float, nullable=False)  # 年龄
    hypertension = Column(Integer, default=0)  # 高血压（0/1）
    heart_disease = Column(Integer, default=0)  # 心脏病（0/1）
    ever_married = Column(String(10))  # 婚姻状况
    work_type = Column(String(50))  # 工作类型
    residence_type = Column(String(20))  # 居住类型
    avg_glucose_level = Column(Float)  # 平均血糖水平
    bmi = Column(Float)  # BMI指数
    smoking_status = Column(String(50))  # 吸烟状况
    
    # 预测结果
    risk_score = Column(Float, nullable=False)  # 风险分数（0-1）
    risk_percent = Column(Float, nullable=False)  # 风险百分比（0-100）
    risk_level = Column(String(20), nullable=False)  # 风险等级（safe/warning/danger）
    suggestion = Column(Text)  # 建议
    
    # 预测类型（single/batch）
    prediction_type = Column(String(20), default='single')
    
    # 批次ID（用于批量预测）
    batch_id = Column(String(50))
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now())
    
    # 额外信息（JSON格式）
    extra_info = Column(JSON)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'gender': self.gender,
            'age': self.age,
            'hypertension': self.hypertension,
            'heart_disease': self.heart_disease,
            'ever_married': self.ever_married,
            'work_type': self.work_type,
            'residence_type': self.residence_type,
            'avg_glucose_level': self.avg_glucose_level,
            'bmi': self.bmi,
            'smoking_status': self.smoking_status,
            'risk_score': self.risk_score,
            'risk_percent': self.risk_percent,
            'risk_level': self.risk_level,
            'suggestion': self.suggestion,
            'prediction_type': self.prediction_type,
            'batch_id': self.batch_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

