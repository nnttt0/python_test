"""可视化服务"""
import io
import base64
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from config import Config

plt.rcParams['font.sans-serif'] = Config.MATPLOTLIB_FONT
plt.rcParams['axes.unicode_minus'] = False


class Visualizer:
    """图表生成器"""
    
    @staticmethod
    def _fig_to_base64(fig) -> str:
        """将matplotlib图形转换为base64字符串"""
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')  # 提高DPI从100到150
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        return img_base64
    
    @staticmethod
    def create_histogram(df: pd.DataFrame, column: str = 'age') -> str:
        """直方图"""
        fig, ax = plt.subplots(figsize=(12, 7))  # 增大尺寸
        df[column].hist(bins=20, ax=ax, color='steelblue', edgecolor='black')
        
        # 翻译列名为中文
        column_names = {
            'age': '年龄',
            'avg_glucose_level': '血糖水平',
            'bmi': 'BMI指数'
        }
        cn_name = column_names.get(column, column)
        
        ax.set_title(f'{cn_name}分布直方图', fontsize=16, fontweight='bold', pad=15)
        ax.set_xlabel(cn_name, fontsize=13)
        ax.set_ylabel('频数', fontsize=13)
        ax.tick_params(labelsize=11)
        return Visualizer._fig_to_base64(fig)
    
    @staticmethod
    def create_boxplot(df: pd.DataFrame, predictions: list = None) -> str:
        """箱线图"""
        fig, ax = plt.subplots(figsize=(12, 7))  # 增大尺寸
        
        if 'stroke' in df.columns:
            df['stroke_label'] = df['stroke'].map({0: '未中风', 1: '中风'})
            df.boxplot(column='avg_glucose_level', by='stroke_label', ax=ax)
            ax.set_title('中风与血糖水平关系', fontsize=16, fontweight='bold', pad=15)
            ax.set_xlabel('是否中风', fontsize=13)
            ax.set_ylabel('平均血糖水平 (mg/dL)', fontsize=13)
        else:
            df['risk_label'] = pd.cut(
                predictions, 
                bins=[0, 0.3, 0.5, 1],
                labels=['低风险', '中风险', '高风险']
            )
            df.boxplot(column='avg_glucose_level', by='risk_label', ax=ax)
            ax.set_title('血糖水平与风险等级关系', fontsize=16, fontweight='bold', pad=15)
            ax.set_xlabel('风险等级', fontsize=13)
            ax.set_ylabel('平均血糖水平 (mg/dL)', fontsize=13)
            plt.xticks(rotation=45)
        
        ax.tick_params(labelsize=11)
        return Visualizer._fig_to_base64(fig)
    
    @staticmethod
    def create_correlation_heatmap(df: pd.DataFrame) -> str:
        """相关性热力图"""
        fig, ax = plt.subplots(figsize=(12, 10))  # 增大尺寸
        numeric_df = df.select_dtypes(include=['number'])
        corr = numeric_df.corr()
        sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm', ax=ax,
                   annot_kws={'size': 11}, linewidths=0.5)
        ax.set_title('特征相关性热力图', fontsize=16, fontweight='bold', pad=15)
        ax.tick_params(labelsize=11)
        return Visualizer._fig_to_base64(fig)
    
    @staticmethod
    def create_bar_chart(df: pd.DataFrame, predictions: list = None) -> str:
        """条形图"""
        fig, ax = plt.subplots(figsize=(12, 7))  # 增大尺寸
        
        if 'work_type' in df.columns and 'stroke' in df.columns:
            stroke_by_work = df.groupby('work_type')['stroke'].mean() * 100
            stroke_by_work.plot(kind='bar', ax=ax, color='coral')
            ax.set_title('不同工作类型的中风率', fontsize=16, fontweight='bold', pad=15)
            ax.set_xlabel('工作类型', fontsize=13)
            ax.set_ylabel('中风率 (%)', fontsize=13)
        else:
            df['risk_level'] = pd.cut(
                predictions, 
                bins=[0, 0.3, 0.5, 1],
                labels=['低风险', '中风险', '高风险']
            )
            risk_by_work = df.groupby('work_type')['risk_level'].apply(
                lambda x: (x == '高风险').sum() / len(x) * 100
            )
            risk_by_work.plot(kind='bar', ax=ax, color='coral')
            ax.set_title('不同工作类型的高风险比例', fontsize=16, fontweight='bold', pad=15)
            ax.set_xlabel('工作类型', fontsize=13)
            ax.set_ylabel('高风险比例 (%)', fontsize=13)
        
        plt.xticks(rotation=45, fontsize=11)
        ax.tick_params(labelsize=11)
        return Visualizer._fig_to_base64(fig)
    
    @staticmethod
    def create_pie_chart(predictions: list) -> str:
        """饼图"""
        fig, ax = plt.subplots(figsize=(12, 8))  # 增大尺寸
        
        risk_levels = []
        for p in predictions:
            if p >= 0.5:
                risk_levels.append('高风险')
            elif p >= 0.3:
                risk_levels.append('中风险')
            else:
                risk_levels.append('低风险')
        
        high_count = risk_levels.count('高风险')
        medium_count = risk_levels.count('中风险')
        low_count = risk_levels.count('低风险')
        
        sizes = [high_count, medium_count, low_count]
        labels = ['高风险', '中风险', '低风险']
        colors = ['#F53F3F', '#FF7D00', '#00B42A']
        explode = (0.05, 0, 0)
        
        wedges, texts, autotexts = ax.pie(
            sizes, explode=explode, labels=labels, colors=colors,
            autopct='%1.1f%%', startangle=90, textprops={'fontsize': 14}
        )
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(13)
        
        # 设置图例字体大小
        for text in texts:
            text.set_fontsize(13)
        
        ax.set_title('风险等级分布', fontsize=16, fontweight='bold', pad=15)
        return Visualizer._fig_to_base64(fig)
    
    @staticmethod
    def create_line_chart(df: pd.DataFrame, predictions: list) -> str:
        """折线图"""
        import numpy as np
        fig, ax = plt.subplots(figsize=(12, 7))  # 增大尺寸
        
        # 将 predictions 转换为 numpy 数组
        predictions_array = np.array(predictions)
        
        age_groups = df.groupby(pd.cut(df['age'], bins=range(0, 101, 10)), observed=False)
        age_risk = []
        for group, subset in age_groups:
            if len(subset) > 0:
                # 使用 subset.index 获取索引，然后从 predictions_array 中取值
                avg_risk = predictions_array[subset.index].mean() * 100
                age_risk.append(avg_risk)
        
        age_bins = [f'{i}-{i + 9}' for i in range(0, 100, 10)]
        ax.plot(age_bins[:len(age_risk)], age_risk, marker='o', linewidth=2.5, color='#4E6CF7', markersize=8)
        ax.set_title('年龄与中风风险趋势', fontsize=16, fontweight='bold', pad=15)
        ax.set_xlabel('年龄段', fontsize=13)
        ax.set_ylabel('平均风险概率 (%)', fontsize=13)
        ax.tick_params(labelsize=11)
        plt.xticks(rotation=45, fontsize=11)
        
        return Visualizer._fig_to_base64(fig)
    
    @staticmethod
    def create_cluster_scatter(df: pd.DataFrame, cluster_labels: list, cluster_centers: list = None, feature_names: list = None) -> str:
        """聚类散点图（使用PCA降维展示所有特征）"""
        from sklearn.decomposition import PCA
        from sklearn.preprocessing import StandardScaler
        
        fig, axes = plt.subplots(1, 2, figsize=(18, 8))  # 增大尺寸
        
        # 选择数值列
        numeric_df = df.select_dtypes(include=['number'])
        
        # 标准化数据
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(numeric_df)
        
        # PCA降维到2D
        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X_scaled)
        
        # 左图：PCA降维后的聚类结果
        ax1 = axes[0]
        unique_clusters = sorted(list(set(cluster_labels)))
        colors = plt.cm.Set1(range(len(unique_clusters)))
        
        for i, cluster_id in enumerate(unique_clusters):
            mask = [c == cluster_id for c in cluster_labels]
            ax1.scatter(
                X_pca[mask, 0],
                X_pca[mask, 1],
                c=[colors[i]],
                label=f'簇 {cluster_id}',
                s=180,  # 增大数据点
                alpha=0.7,
                edgecolors='w',
                linewidth=1.5,
                zorder=5
            )
            
            # 标注簇中心
            if cluster_centers and i < len(cluster_centers):
                center_pca = pca.transform([cluster_centers[i]])
                ax1.scatter(
                    center_pca[0, 0],
                    center_pca[0, 1],
                    c='red',
                    marker='X',
                    s=300,  # 增大中心点
                    edgecolors='black',
                    linewidth=2.5,
                    zorder=10
                )
        
        explained_var = pca.explained_variance_ratio_
        ax1.set_title(
            f'K-Means 聚类分析（PCA降维）\n'
            f'PC1: {explained_var[0]*100:.1f}%, PC2: {explained_var[1]*100:.1f}%',
            fontsize=16,  # 增大字体
            fontweight='bold',
            pad=15
        )
        ax1.set_xlabel(f'第一主成分 (PC1)\n解释方差: {explained_var[0]*100:.1f}%', fontsize=13)
        ax1.set_ylabel(f'第二主成分 (PC2)\n解释方差: {explained_var[1]*100:.1f}%', fontsize=13)
        ax1.legend(loc='best', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.axhline(y=0, color='gray', linewidth=0.5, linestyle='--')
        ax1.axvline(x=0, color='gray', linewidth=0.5, linestyle='--')
        ax1.tick_params(labelsize=11)
        
        # 右图：特征重要性热图（每个簇的特征均值）
        ax2 = axes[1]
        if feature_names:
            # 计算每个簇的特征均值
            cluster_means = []
            for cluster_id in unique_clusters:
                mask = [c == cluster_id for c in cluster_labels]
                cluster_data = numeric_df[mask]
                cluster_means.append(cluster_data.mean().values)
            
            # 标准化特征值以便比较
            cluster_means_array = np.array(cluster_means)
            cluster_means_std = (cluster_means_array - cluster_means_array.mean(axis=0)) / (cluster_means_array.std(axis=0) + 1e-8)
            
            # 绘制热图
            im = ax2.imshow(cluster_means_std, cmap='RdYlBu_r', aspect='auto', interpolation='nearest')
            
            # 设置坐标轴
            ax2.set_yticks(range(len(unique_clusters)))
            ax2.set_yticklabels([f'簇 {i}' for i in unique_clusters], fontsize=12)
            ax2.set_xticks(range(len(feature_names)))
            ax2.set_xticklabels(feature_names, rotation=45, ha='right', fontsize=11)
            
            # 添加数值标注
            for i in range(len(unique_clusters)):
                for j in range(len(feature_names)):
                    text = ax2.text(j, i, f'{cluster_means_array[i, j]:.1f}',
                                  ha='center', va='center', color='black', fontsize=9)
            
            ax2.set_title('各簇特征均值（标准化后）', fontsize=16, fontweight='bold', pad=15)
            
            # 添加颜色条
            cbar = plt.colorbar(im, ax=ax2)
            cbar.set_label('标准化值', fontsize=11)
            cbar.ax.tick_params(labelsize=10)
        
        plt.tight_layout(pad=2.0)
        return Visualizer._fig_to_base64(fig)
