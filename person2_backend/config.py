"""系统配置文件"""
import os

class Config:
    """基础配置"""
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 最大16MB
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
    
    # 模型路径
    MODEL_PATH = 'model/model.pkl'
    FEATURE_COLUMNS_PATH = 'model/feature_columns.pkl'
    
    # 编码映射
    GENDER_MAP = {'Male': 0, 'Female': 1, 'Other': 2}
    MARRIED_MAP = {'Yes': 1, 'No': 0}
    RESIDENCE_MAP = {'Urban': 1, 'Rural': 0}
    WORK_TYPE_MAP = {
        "Private": 0, 
        "Self-employed": 1, 
        "Govt_job": 2, 
        "children": 3, 
        "Never_worked": 4
    }
    SMOKING_MAP = {
        'never smoked': 0, 
        'formerly smoked': 1, 
        'smokes': 2, 
        'Unknown': 3
    }
    
    # 风险阈值
    HIGH_RISK_THRESHOLD = 0.5
    MEDIUM_RISK_THRESHOLD = 0.3
    
    # matplotlib配置
    MATPLOTLIB_FONT = ['Microsoft YaHei', 'SimHei', 'SimSun', 'Arial Unicode MS']
