import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='sklearn')

from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import Config
from person3_ml_services.models.predictor import StrokePredictor
from person3_ml_services.models.cluster import ClusterAnalyzer
from person3_ml_services.services.data_processor import DataProcessor
from person3_ml_services.services.visualizer import Visualizer
from person4_database_frontend.database import init_db, get_db, PredictionService
from person4_database_frontend.database.db import SessionLocal

app = Flask(__name__)
app.config.from_object(Config)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 初始化数据库
init_db()

# 初始化模型和服务
predictor = StrokePredictor()
data_processor = DataProcessor()
visualizer = Visualizer()

print("    系统启动成功！")
print(f"   模型类型: {type(predictor.model).__name__}")
print(f"   特征列: {predictor.feature_columns}")


@app.route('/')
def index():
    """首页"""
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def predict():
    """单条预测"""
    try:
        # 获取表单数据并处理
        input_data = data_processor.prepare_input_data(request.form)

        # 转换为 DataFrame
        input_df = pd.DataFrame([input_data])[predictor.feature_columns]

        # 预测概率
        result = predictor.predict_single(input_data)
        risk = result['risk']
        risk_percent = result['risk_percent']

        # 风险等级和建议
        if risk >= 0.5:
            level = "danger"
            suggestion = "高风险！建议立即就医检查"
            message = "您的风险评估结果为高风险，请尽快咨询专业医生。"
        elif risk >= 0.3:
            level = "warning"
            suggestion = "中等风险，建议改善生活习惯，定期体检"
            message = "您的风险评估结果为中等风险，请注意健康管理。"
        else:

            level = "safe"
            suggestion = "低风险，保持良好的生活习惯"
            message = "您的风险评估结果为低风险，请继续保持健康生活。"

        # 保存到数据库
        db = SessionLocal()
        try:
            PredictionService.save_single_prediction(db, input_data, {
                'risk': risk,
                'risk_percent': risk_percent,
                'level': level,
                'suggestion': suggestion
            })
        except Exception as db_error:
            print(f"  保存到数据库失败: {db_error}")
        finally:
            db.close()

        return jsonify({
            'success': True,
            'risk': risk,
            'risk_percent': risk_percent,
            'level': level,
            'suggestion': suggestion,
            'message': message
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/upload', methods=['POST'])
def upload():
    """批量预测"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '请选择文件'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': '请选择文件'})

    try:
        # 读取用户上传的文件（支持CSV和Excel）
        df = data_processor.load_file(file, file.filename)
        original_df = df.copy()

        # 数据清洗
        df = data_processor.clean_data(df)

        # 编码分类变量
        df = data_processor.encode_categorical(df)

        # 批量预测
        predictions = predictor.predict_batch(df)

        # 添加预测结果
        original_df['中风风险概率'] = [(p * 100) for p in predictions]
        original_df['风险等级'] = [data_processor.classify_risk(p) for p in predictions]
        
        # 将英文列名映射为中文（用于显示）
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
        
        # 创建用于显示的DataFrame（复制一份并修改列名）
        df_display = original_df.copy()
        df_display.rename(columns=column_name_map, inplace=True)

        # 统计信息
        high_count = sum(1 for p in predictions if p >= Config.HIGH_RISK_THRESHOLD)
        medium_count = sum(1 for p in predictions if Config.MEDIUM_RISK_THRESHOLD <= p < Config.HIGH_RISK_THRESHOLD)
        low_count = sum(1 for p in predictions if p < Config.MEDIUM_RISK_THRESHOLD)

        # 转换为 HTML 表格（只显示前50行，使用中文列名）
        html_table = df_display.head(50).to_html(classes='table table-striped', index=False)

        # 关键修复：将 NaN 替换为 None，确保 JSON 序列化正确
        records = df_display.to_dict('records')
        for record in records:
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None

        return jsonify({
            'success': True,
            'total': len(df),
            'high_count': int(high_count),
            'medium_count': int(medium_count),
            'low_count': int(low_count),
            'html_table': html_table,
            'columns': df_display.columns.tolist(),
            'data': records
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/export', methods=['POST'])
def export():
    """导出预测结果"""
    try:
        data = request.json
        df = pd.DataFrame(data)

        # 转换为 CSV
        csv_data = df.to_csv(index=False, encoding='utf-8-sig')

        return jsonify({
            'success': True,
            'csv_data': csv_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/get_data_summary', methods=['POST'])
def get_data_summary():
    """获取数据摘要（用于可视化）"""
    try:
        file = request.files['file']
        if not file:
            return jsonify({'success': False, 'error': '请选择文件'})

        df = pd.read_csv(file)

        # 基础统计
        summary = {
            'total': len(df),
            'columns': df.columns.tolist(),
            'numeric_columns': df.select_dtypes(include=['number']).columns.tolist(),
            'categorical_columns': df.select_dtypes(include=['object']).columns.tolist()
        }

        # 年龄分布统计
        if 'age' in df.columns:
            summary['age_stats'] = {
                'min': float(df['age'].min()),
                'max': float(df['age'].max()),
                'mean': float(df['age'].mean()),
                'median': float(df['age'].median())
            }

        # 血糖分布统计
        if 'avg_glucose_level' in df.columns:
            summary['glucose_stats'] = {
                'min': float(df['avg_glucose_level'].min()),
                'max': float(df['avg_glucose_level'].max()),
                'mean': float(df['avg_glucose_level'].mean())
            }

        # 中风比例
        if 'stroke' in df.columns:
            stroke_count = df['stroke'].sum()
            summary['stroke_rate'] = round(stroke_count / len(df) * 100, 2)

        return jsonify({'success': True, 'summary': summary})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/generate_chart', methods=['POST'])
def generate_chart():
    """生成图表"""
    try:
        data = request.json
        chart_type = data.get('chart_type')
        file_data = data.get('file_data')

        # 从 CSV 数据重建 DataFrame
        df = pd.read_csv(pd.io.common.StringIO(file_data))
        original_df = df.copy()

        # 数据清洗（与批量预测保持一致）
        df = data_processor.clean_data(df)

        # 编码分类变量
        df = data_processor.encode_categorical(df)

        # 选择特征列并预测（饼图需要）
        predictions = predictor.predict_batch(df)

        # 根据图表类型生成
        if chart_type == 'histogram':
            column = data.get('column', 'age')
            img_base64 = visualizer.create_histogram(df, column)
        elif chart_type == 'boxplot':
            img_base64 = visualizer.create_boxplot(df, predictions)
        elif chart_type == 'correlation':
            img_base64 = visualizer.create_correlation_heatmap(df)
        elif chart_type == 'bar':
            img_base64 = visualizer.create_bar_chart(df, predictions)
        elif chart_type == 'pie':
            img_base64 = visualizer.create_pie_chart(predictions)
        elif chart_type == 'line':
            img_base64 = visualizer.create_line_chart(df, predictions)
        else:
            return jsonify({'success': False, 'error': f'不支持的图表类型: {chart_type}'})

        return jsonify({'success': True, 'image': img_base64})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})


@app.route('/cluster', methods=['POST'])
def cluster_analysis():
    """K-Means聚类分析"""
    try:
        data = request.json
        file_data = data.get('file_data')
        n_clusters = int(data.get('n_clusters', 3))
        
        # 从 CSV 数据重建 DataFrame
        df = pd.read_csv(pd.io.common.StringIO(file_data))
        
        # 数据清洗
        df_clean = data_processor.clean_data(df)
        
        # 选择数值列进行聚类
        numeric_cols = df_clean.select_dtypes(include=['number']).columns.tolist()
        
        # 将英文列名映射为中文（用于显示）
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
        numeric_cols_cn = [column_name_map.get(col, col) for col in numeric_cols]
        
        # 执行聚类
        analyzer = ClusterAnalyzer(n_clusters=n_clusters)
        result = analyzer.fit_predict(df_clean, numeric_cols)
        
        # 生成聚类可视化图表（使用中文列名）
        cluster_labels = result['cluster_labels']
        cluster_centers = result.get('cluster_centers', None)
        img_base64 = visualizer.create_cluster_scatter(
            df_clean, 
            cluster_labels,
            cluster_centers=cluster_centers,
            feature_names=numeric_cols_cn
        )
        
        # 添加聚类特征说明（使用中文列名）
        result['cluster_features'] = numeric_cols_cn
        
        # 计算每个簇的中心点特征（用于解释簇的含义）
        if 'cluster_centers' in result:
            cluster_centers_info = []
            for i, center in enumerate(result['cluster_centers']):
                center_dict = {}
                for j, col in enumerate(numeric_cols_cn):
                    if j < len(center):
                        center_dict[col] = round(float(center[j]), 2)
                cluster_centers_info.append({
                    'cluster_id': i,
                    'size': result['cluster_sizes'].get(str(i), 0),
                    'center': center_dict
                })
            result['cluster_centers_info'] = cluster_centers_info
        
        return jsonify({
            'success': True, 
            'result': result,
            'image': img_base64  # 添加聚类图表
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})


if __name__ == '__main__':
    app.run(debug=True, port=8888)
