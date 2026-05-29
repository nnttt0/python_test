"""K-Means聚类分析"""
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import pandas as pd


class ClusterAnalyzer:
    """聚类分析器"""
    
    def __init__(self, n_clusters=3):
        self.n_clusters = n_clusters
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        self.scaler = StandardScaler()
    
    def fit_predict(self, df: pd.DataFrame, numeric_cols: list = None) -> dict:
        """
        执行聚类分析
        :param df: 原始数据
        :param numeric_cols: 数值列名列表，None则自动选择
        :return: 聚类结果
        """
        if numeric_cols is None:
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if not numeric_cols:
            raise ValueError("没有找到数值型列")
        
        X = df[numeric_cols].dropna()
        
        if len(X) == 0:
            raise ValueError("没有有效数据用于聚类")
        
        X_scaled = self.scaler.fit_transform(X)
        clusters = self.kmeans.fit_predict(X_scaled)
        
        result_df = X.copy()
        result_df['cluster'] = clusters
        
        cluster_stats = {
            'total': len(result_df),
            'n_clusters': self.n_clusters,
            'cluster_sizes': result_df['cluster'].value_counts().to_dict(),
            'cluster_centers': self.kmeans.cluster_centers_.tolist(),
            'cluster_labels': clusters.tolist(),  # 添加聚类标签
            'data': result_df.reset_index().to_dict('records')
        }
        
        return cluster_stats
    
    def get_optimal_clusters(self, df: pd.DataFrame, numeric_cols: list) -> int:
        """肘部法则计算最佳聚类数"""
        from sklearn.metrics import silhouette_score
        
        inertias = []
        silhouette_scores = []
        K_range = range(2, min(11, len(df)))
        
        for k in K_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            X_scaled = self.scaler.fit_transform(df[numeric_cols].dropna())
            labels = kmeans.fit_predict(X_scaled)
            
            inertias.append(kmeans.inertia_)
            silhouette_scores.append(silhouette_score(X_scaled, labels))
        
        best_k = list(K_range)[silhouette_scores.index(max(silhouette_scores))]
        return best_k
