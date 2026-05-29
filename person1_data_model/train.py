import pandas as pd
import pickle
import os
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix


class StrokeModel:
    """中风预测模型训练类"""

    def __init__(self, data_path):
        self.data_path = data_path
        self.df = None
        self.model = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        # 获取项目根目录
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def load_cleaned_data(self):
        """加载清洗后的数据"""
        self.df = pd.read_csv(self.data_path)

        print(f"   加载成功！")
        print(f"   数据行数: {len(self.df)}")
        print(f"   数据列数: {len(self.df.columns)}")
        print(f"   列名: {self.df.columns.tolist()}")

    def prepare_data(self):
        """准备数据（分离特征和目标）"""
        # 获取所有列名
        all_columns = self.df.columns.tolist()
        # 排除'stroke'列
        feature_columns = [col for col in all_columns if col != 'stroke']
        # 分离特征和目标列
        x = self.df[feature_columns]
        y = self.df['stroke']
        # 划分训练集和测试集（80% 训练，20% 测试）,random_state保证划分结果每次相同
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            x, y, test_size=0.2, random_state=40
        )

        print(f"训练集大小: {len(self.X_train)}")
        print(f"测试集大小: {len(self.X_test)}")
        print(f"训练集中风样本: {self.y_train.sum()}")
        print(f"测试集中风样本: {self.y_test.sum()}")

    def train_model(self):
        """训练模型"""
        # 创建逻辑回归模型
        self.model = LogisticRegression(max_iter=1000, random_state=40, class_weight={0: 1, 1: 18})
        # self.model = RandomForestClassifier(
        #     min_samples_split=4,  # 分裂所需最小样本数
        #     n_estimators=150,  # 决策树的数量
        #     max_depth=10,  # 每棵树的最大深度
        #     class_weight={0: 1, 1: 20},  # 类别权重（0=正常，1=中风）
        #     random_state=40  # 随机种子
        # )
        # 训练
        self.model.fit(self.X_train, self.y_train)
        print("模型训练完成！")

    def evaluate_model(self):
        """评估模型"""
        # 在测试集上预测
        y_pred = self.model.predict(self.X_test)

        # 计算准确率
        accuracy = accuracy_score(self.y_test, y_pred)
        print(f"模型准确率: {accuracy * 100:.2f}%")

        # 打印详细报告
        print("\n分类报告:")
        print(classification_report(self.y_test, y_pred,
                                    target_names=['未中风', '中风']))

        # 打印混淆矩阵
        print("混淆矩阵:")
        cm = confusion_matrix(self.y_test, y_pred)
        print(f"           预测未中风  预测中风")
        print(f"实际未中风:     {cm[0, 0]}        {cm[0, 1]}")
        print(f"实际中风:       {cm[1, 0]}        {cm[1, 1]}")

        return accuracy

    def save_model(self, model_path=None):
        """保存模型"""
        if model_path is None:
            model_dir = os.path.join(self.project_root, 'model')
            model_path = os.path.join(model_dir, 'model.pkl')
        
        # 确保model目录存在
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        with open(model_path, 'wb') as f:
            pickle.dump(self.model, f)

        print(f"模型已保存到: {model_path}")

        # 同时保存特征列名（预测时需要）
        feature_cols = list(self.X_train.columns)
        feature_path = os.path.join(self.project_root, 'model', 'feature_columns.pkl')
        with open(feature_path, 'wb') as f:
            pickle.dump(feature_cols, f)
        print(f"特征列名已保存到: {feature_path}")

    def run_all(self):
        """运行完整训练流程"""
        self.load_cleaned_data()
        self.prepare_data()
        self.train_model()
        self.evaluate_model()
        self.save_model()


if __name__ == "__main__":
    # 获取项目根目录的绝对路径
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(project_root, 'DataSet', 'stroke_data_cleaned.csv')
    trainer = StrokeModel(data_path)
    trainer.run_all()
