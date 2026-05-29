"""数据处理服务"""
import pandas as pd
from config import Config


class DataProcessor:
    """数据处理器"""
    
    @staticmethod
    def load_file(file, filename: str) -> pd.DataFrame:
        """
        加载CSV或Excel文件
        :param file: 文件对象
        :param filename: 文件名
        :return: DataFrame
        """
        ext = filename.rsplit('.', 1)[1].lower()
        
        if ext == 'csv':
            return pd.read_csv(file)
        elif ext in ['xlsx', 'xls']:
            return pd.read_excel(file)
        else:
            raise ValueError(f"不支持的文件格式: {ext}")
    
    @staticmethod
    def clean_data(df: pd.DataFrame) -> pd.DataFrame:
        """
        清洗数据
        :param df: 原始DataFrame
        :return: 清洗后的DataFrame
        """
        df_clean = df.copy()
        
        if 'id' in df_clean.columns:
            df_clean = df_clean.drop('id', axis=1)
        
        df_clean['bmi'] = pd.to_numeric(df_clean['bmi'], errors='coerce')
        df_clean['bmi'] = df_clean['bmi'].fillna(df_clean['bmi'].median())
        
        return df_clean
    
    @staticmethod
    def encode_categorical(df: pd.DataFrame) -> pd.DataFrame:
        """
        编码分类变量
        :param df: DataFrame
        :return: 编码后的DataFrame
        """
        df_encoded = df.copy()
        
        df_encoded['gender'] = df_encoded['gender'].map(Config.GENDER_MAP)
        df_encoded['ever_married'] = df_encoded['ever_married'].map(Config.MARRIED_MAP)
        df_encoded['Residence_type'] = df_encoded['Residence_type'].map(Config.RESIDENCE_MAP)
        df_encoded['work_type'] = df_encoded['work_type'].map(Config.WORK_TYPE_MAP)
        df_encoded['smoking_status'] = df_encoded['smoking_status'].map(Config.SMOKING_MAP)
        
        return df_encoded
    
    @staticmethod
    def prepare_input_data(form_data: dict) -> dict:
        """
        准备单条预测的输入数据
        :param form_data: 表单数据
        :return: 处理后的输入数据
        """
        return {
            'gender': Config.GENDER_MAP[form_data['gender']],
            'age': float(form_data['age']),
            'hypertension': int(form_data['hypertension']),
            'heart_disease': int(form_data['heart_disease']),
            'ever_married': Config.MARRIED_MAP[form_data['ever_married']],
            'work_type': Config.WORK_TYPE_MAP[form_data['work_type']],
            'Residence_type': Config.RESIDENCE_MAP[form_data['Residence_type']],
            'avg_glucose_level': float(form_data['avg_glucose_level']),
            'bmi': float(form_data['bmi']) if form_data.get('bmi') else 25.0,
            'smoking_status': Config.SMOKING_MAP[form_data['smoking_status']]
        }
    
    @staticmethod
    def classify_risk(probability: float) -> str:
        """根据概率分类风险等级"""
        if probability >= Config.HIGH_RISK_THRESHOLD:
            return '高风险'
        elif probability >= Config.MEDIUM_RISK_THRESHOLD:
            return '中风险'
        else:
            return '低风险'
    
    @staticmethod
    def get_data_summary(df: pd.DataFrame) -> dict:
        """获取数据摘要"""
        summary = {
            'total': len(df),
            'columns': df.columns.tolist(),
            'numeric_columns': df.select_dtypes(include=['number']).columns.tolist(),
            'categorical_columns': df.select_dtypes(include=['object']).columns.tolist()
        }
        
        # 列名映射为中文
        column_name_map = {
            'gender': '性别',
            'age': '年龄',
            'hypertension': '高血压',
            'heart_disease': '心脏病',
            'ever_married': '婚姻状况',
            'work_type': '工作类型',
            'Residence_type': '居住类型',
            'avg_glucose_level': '平均血糖水平',
            'bmi': 'BMI指数',
            'smoking_status': '吸烟状况',
            'stroke': '是否中风'
        }
        
        # 转换数值列名为中文
        summary['numeric_columns_cn'] = [
            column_name_map.get(col, col) for col in summary['numeric_columns']
        ]
        summary['categorical_columns_cn'] = [
            column_name_map.get(col, col) for col in summary['categorical_columns']
        ]
        
        if 'age' in df.columns:
            summary['age_stats'] = {
                'min': float(df['age'].min()),
                'max': float(df['age'].max()),
                'mean': float(df['age'].mean()),
                'median': float(df['age'].median())
            }
        
        if 'avg_glucose_level' in df.columns:
            summary['glucose_stats'] = {
                'min': float(df['avg_glucose_level'].min()),
                'max': float(df['avg_glucose_level'].max()),
                'mean': float(df['avg_glucose_level'].mean())
            }
        
        if 'stroke' in df.columns:
            stroke_count = df['stroke'].sum()
            summary['stroke_rate'] = round(stroke_count / len(df) * 100, 2)
        
        return summary
