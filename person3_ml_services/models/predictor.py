"""中风预测模型"""
import warnings
warnings.filterwarnings('ignore')

import pickle
import pandas as pd
from config import Config


class StrokePredictor:
    """中风预测器"""
    
    def __init__(self):
        self.model = None
        self.feature_columns = None
        self._load_model()
    
    def _load_model(self):
        """加载训练好的模型"""
        with open(Config.MODEL_PATH, 'rb') as f:
            self.model = pickle.load(f)
        
        with open(Config.FEATURE_COLUMNS_PATH, 'rb') as f:
            self.feature_columns = pickle.load(f)
    
    def predict_single(self, input_data: dict) -> dict:
        """
        单条预测
        :param input_data: 输入数据字典
        :return: 预测结果
        """
        input_df = pd.DataFrame([input_data])[self.feature_columns]
        risk = self.model.predict_proba(input_df)[0][1]
        
        return {
            'risk': float(risk),
            'risk_percent': round(float(risk) * 100, 2)
        }
    
    def predict_batch(self, df: pd.DataFrame) -> list:
        """
        批量预测
        :param df: 处理后的DataFrame
        :return: 预测概率列表
        """
        X = df[self.feature_columns]
        predictions = self.model.predict_proba(X)[:, 1]
        return predictions.tolist()
    
    def get_feature_columns(self) -> list:
        """获取特征列名"""
        return self.feature_columns.copy()
