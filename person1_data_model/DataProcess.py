import pandas as pd
import os


class DataProcess:
    """数据清洗和处理类"""

    def __init__(self, file_path):
        """
        初始化方法
        保存文件路径，初始化 df 变量
        """
        self.file_path = file_path
        self.df = None
        # 记录数据表的行数和列数
        self.shape = None
        # 记录特征列名
        self.feature_columns = None
        self.X_df = None
        self.y_df = None
        # 获取项目根目录
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def load_data(self):
        """
        加载数据方法
        读取 CSV 文件，保存到 self.df
        """
        print("正在将数据加载进来")
        # 通过pd读取csv文件转为dataframe形式
        self.df = pd.read_csv(self.file_path)
        self.shape = self.df.shape  # shape是元组形式的

        # 因为id与原因统计无关，所有直接删除该列
        if 'id' in self.df.columns:
            self.df = self.df.drop('id', axis=1)
        print(f' 数据的行数：{self.shape[0]}')
        print(f' 数据的列数：{self.shape[1]}')
        print(f'数据列的属性：{self.df.columns.tolist()}')
        print("完成")

    def check_missing(self):
        """
        检查缺失值方法
        查看每列的缺失值数量
        """
        missing = self.df.isnull().sum()

        has_missing = False
        for col in self.df.columns:
            if missing[col] > 0:
                print(f"   {col}: {missing[col]} 个缺失")
                has_missing = True
        # 返回是否有缺失值和每列缺失值数量，方便处理
        return has_missing, missing

    def handle_missing_bmi(self):
        """
        处理 bmi 缺失值方法
        用中位数填充 bmi 列的缺失值
        """
        # 将bmi列转为数字（'N/A' 会变成 NaN）
        # errors='coerce'确保无法转换的变为NaN
        self.df['bmi'] = pd.to_numeric(self.df['bmi'], errors='coerce')
        # 计算中位数并填充
        median_val = self.df['bmi'].median()
        self.df['bmi'] = self.df['bmi'].fillna(median_val)

        print(f"使用的中位数: {median_val}")

    def encode_all_columns(self):
        """
        将性别等文字转为数字，方便后续统计
        """
        gender_mp = {'Male': 0, 'Female': 1, 'Other': 2}
        married_mp = {'Yes': 1, 'No': 0}
        residence_mp = {'Urban': 1, 'Rural': 0}
        work_type_mp = {"Private": 0, "Self-employed": 1, "Govt_job": 2, "children": 3, "Never_worked": 4}
        smoking_mp = {'never smoked': 0, 'formerly smoked': 1, 'smokes': 2, 'Unknown': 3}

        self.df['gender'] = self.df['gender'].map(gender_mp)
        self.df['ever_married'] = self.df['ever_married'].map(married_mp)
        self.df['Residence_type'] = self.df['Residence_type'].map(residence_mp)
        self.df['work_type'] = self.df['work_type'].map(work_type_mp)
        self.df['smoking_status'] = self.df['smoking_status'].map(smoking_mp)

    def split_features_target(self):
        """
        分离特征和目标变量
        将数据分为 X（特征）和 y（目标）
        """
        # 获取所有列名
        all_columns = self.df.columns.tolist()
        # 排除'stroke'列
        self.feature_columns = [col for col in all_columns if col != 'stroke']
        # 分离特征和目标列
        self.X_df = self.df[self.feature_columns]
        self.y_df = self.df['stroke']

    def save_cleaned_data(self, output_path=None):
        """
        保存清洗后的数据
        将 self.df 保存为 CSV 文件
        """
        if output_path is None:
            output_path = os.path.join(self.project_root, 'DataSet', 'stroke_data_cleaned.csv')
        # index=False不保存索引
        self.df.to_csv(output_path, index=False)

    def run_all(self):
        """
        运行完整流程
        按顺序调用所有处理方法
        """
        self.load_data()  # 下载数据
        has, miss = self.check_missing()  # 检查缺失情况
        print(has, miss, sep='\n')
        self.handle_missing_bmi()  # 处理bmi的缺失值
        self.encode_all_columns()  # 对数据编码，方便统计处理
        self.split_features_target()  # 分离特征列和目标列
        self.save_cleaned_data()  # 保存数据


# ========== 使用示例 ==========
if __name__ == "__main__":
    # 获取项目根目录的绝对路径
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(project_root, 'DataSet', 'healthcare-dataset-stroke-data.csv')
    processor = DataProcess(file_path)
    processor.run_all()