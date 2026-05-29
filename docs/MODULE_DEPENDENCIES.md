# 模块依赖关系与接口边界说明

**目的**：明确四人分工的文件交叉点，理清调用关系和职责边界

---

## 📊 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    前端层 (人四负责)                          │
│  templates/index.html + static/js/main.js + static/css/     │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP请求 (Fetch API)
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                 路由层 (人二负责)                             │
│                        app.py                                │
│  /predict | /upload | /export | /generate_chart | /cluster  │
└──┬────────────┬──────────────┬──────────────┬───────────────┘
   │            │              │              │
   ↓            ↓              ↓              ↓
┌────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ 模型层  │ │ 服务层    │ │ 服务层    │ │ 数据库层  │
│(人三)   │ │(人三)    │ │(人三)    │ │(人四)    │
│        │ │          │ │          │ │          │
│predic- │ │data_     │ │visual-   │ │db.py     │
│tor.py  │ │processor │ │izer.py   │ │models.py │
│        │ │.py       │ │          │ │services. │
│cluster │ │          │ │          │ │py        │
│.py     │ │          │ │          │ │config.py │
└────────┘ └──────────┘ └──────────┘ └──────────┘
```

---

## 🔗 文件交叉依赖关系图

### 1️⃣ **人一：数据预处理与模型训练**（独立性强）

#### 负责文件
```
DataProcess.py          ← 独立脚本，不依赖其他模块
train.py                ← 独立脚本，不依赖其他模块
DataSet/                ← 原始数据
model/                  ← 训练产物（被其他人使用）
  ├── model.pkl         ← 人三 predictor.py 加载
  └── feature_columns.pkl ← 人三 predictor.py 加载
```

#### 输出产物（供他人使用）
| 产物 | 位置 | 使用者 | 用途 |
|------|------|--------|------|
| `model.pkl` | `model/` | 人三的 `predictor.py` | 加载训练好的模型 |
| `feature_columns.pkl` | `model/` | 人三的 `predictor.py` | 获取特征列名 |
| `stroke_data_cleaned.csv` | `DataSet/` | 可选 | 清洗后的数据 |

#### 依赖关系
```
DataProcess.py → 无依赖（独立运行）
train.py → 依赖 DataProcess.py 的输出
```

**✅ 边界清晰**：人一只负责生成模型文件，不涉及Web应用

---

### 2️⃣ **人二：后端架构与API路由**（核心枢纽）

#### 负责文件
```
app.py                  ← 依赖人三和人四的模块
config.py               ← 全局配置（被人三、人四使用）
requirements.txt        ← 项目依赖
```

#### 调用的模块（交叉点）

##### ✅ 调用【人三】的模块
```python
# app.py 顶部导入
from models.predictor import StrokePredictor      # 人三
from models.cluster import ClusterAnalyzer         # 人三
from services.data_processor import DataProcessor  # 人三
from services.visualizer import Visualizer         # 人三

# 在路由中使用
predictor = StrokePredictor()          # 初始化预测器
data_processor = DataProcessor()       # 初始化管理器
visualizer = Visualizer()              # 初始化可视化器

# 示例：/predict 路由
@app.route('/predict', methods=['POST'])
def predict():
    input_data = data_processor.prepare_input_data(request.form)  # 人三
    result = predictor.predict_single(input_data)                 # 人三
    return jsonify(result)
```

##### ✅ 调用【人四】的模块
```python
# app.py 顶部导入
from database import init_db, get_db, PredictionService  # 人四
from database.db import SessionLocal                     # 人四

# 初始化数据库
init_db()  # 人四

# 示例：保存预测记录
@app.route('/predict', methods=['POST'])
def predict():
    # ... 预测逻辑 ...
    
    db = SessionLocal()  # 人四：获取数据库会话
    try:
        PredictionService.save_single_prediction(db, input_data, result)  # 人四
    finally:
        db.close()
```

#### 对外提供的API接口（供人四的前端调用）

| API端点 | 方法 | 功能 | 调用的人三模块 | 调用的人四模块 |
|---------|------|------|---------------|---------------|
| `/` | GET | 首页 | 无 | 无 |
| `/predict` | POST | 单条预测 | `predictor.predict_single()` | `PredictionService.save_single_prediction()` |
| `/upload` | POST | 批量预测 | `data_processor.*`, `predictor.predict_batch()` | `PredictionService.save_batch_predictions()` |
| `/export` | POST | 导出CSV | 无 | 无 |
| `/generate_chart` | POST | 生成图表 | `visualizer.*` | 无 |
| `/cluster` | POST | 聚类分析 | `ClusterAnalyzer.*`, `visualizer.create_cluster_scatter()` | 无 |

**🔑 关键交叉点**：
- `app.py` 是**集成中心**，协调人三和人四的模块
- 人二需要理解人三和人四的**接口签名**（函数参数和返回值）

---

### 3️⃣ **人三：机器学习模型与业务服务**（被调用方）

#### 负责文件
```
models/predictor.py           ← 被 app.py 调用
models/cluster.py             ← 被 app.py 调用
services/data_processor.py    ← 被 app.py 调用
services/visualizer.py        ← 被 app.py 调用
models/__init__.py            ← 空文件
services/__init__.py          ← 空文件
```

#### 依赖关系

##### ✅ 依赖【人一】的产物
```python
# models/predictor.py
from config import Config

class StrokePredictor:
    def _load_model(self):
        with open(Config.MODEL_PATH, 'rb') as f:  # 'model/model.pkl'
            self.model = pickle.load(f)
        
        with open(Config.FEATURE_COLUMNS_PATH, 'rb') as f:  # 'model/feature_columns.pkl'
            self.feature_columns = pickle.load(f)
```

##### ✅ 依赖【人二】的配置
```python
# models/predictor.py
from config import Config  # 人二的配置文件

# 使用配置
Config.MODEL_PATH              # 模型路径
Config.FEATURE_COLUMNS_PATH    # 特征列路径
Config.HIGH_RISK_THRESHOLD     # 高风险阈值
Config.MEDIUM_RISK_THRESHOLD   # 中风险阈值
```

##### ✅ 依赖第三方库
```python
import pandas as pd
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import seaborn as sns
```

#### 对外提供的接口（供人二调用）

##### 1. `models/predictor.py`
```python
class StrokePredictor:
    def __init__(self):
        """自动加载模型"""
        
    def predict_single(self, input_data: dict) -> dict:
        """
        单条预测
        输入：{'gender': 'Male', 'age': 45, ...}
        返回：{'risk': 0.65, 'risk_percent': 65.0}
        """
        
    def predict_batch(self, df: pd.DataFrame) -> list:
        """
        批量预测
        输入：DataFrame（已清洗和编码）
        返回：[0.65, 0.32, 0.18, ...] 概率列表
        """
        
    def get_feature_columns(self) -> list:
        """返回特征列名列表"""
```

##### 2. `models/cluster.py`
```python
class ClusterAnalyzer:
    def __init__(self, n_clusters=3):
        """初始化聚类器"""
        
    def fit_predict(self, df: pd.DataFrame, numeric_cols: list = None) -> dict:
        """
        执行聚类
        输入：DataFrame + 数值列名
        返回：{
            'total': 500,
            'n_clusters': 3,
            'cluster_sizes': {'0': 200, '1': 180, '2': 120},
            'cluster_centers': [...],
            'cluster_labels': [0, 1, 2, ...],
            'data': [...]
        }
        """
        
    def get_optimal_clusters(self, df: pd.DataFrame, numeric_cols: list) -> int:
        """计算最佳聚类数"""
```

##### 3. `services/data_processor.py`
```python
class DataProcessor:
    def load_file(self, file, filename: str) -> pd.DataFrame:
        """加载CSV或Excel文件"""
        
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """数据清洗（缺失值、异常值）"""
        
    def encode_categorical(self, df: pd.DataFrame) -> pd.DataFrame:
        """分类变量编码"""
        
    def prepare_input_data(self, form_data) -> dict:
        """处理表单数据为模型输入格式"""
        
    def classify_risk(self, probability: float) -> str:
        """根据概率分类风险等级"""
        
    def get_data_summary(self, df: pd.DataFrame) -> dict:
        """获取数据摘要统计"""
```

##### 4. `services/visualizer.py`
```python
class Visualizer:
    def create_histogram(self, df: pd.DataFrame, column: str) -> str:
        """生成直方图，返回Base64字符串"""
        
    def create_boxplot(self, df: pd.DataFrame, predictions: list) -> str:
        """生成箱线图，返回Base64字符串"""
        
    def create_correlation_heatmap(self, df: pd.DataFrame) -> str:
        """生成相关性热力图，返回Base64字符串"""
        
    def create_bar_chart(self, df: pd.DataFrame, predictions: list) -> str:
        """生成条形图，返回Base64字符串"""
        
    def create_pie_chart(self, predictions: list) -> str:
        """生成饼图，返回Base64字符串"""
        
    def create_line_chart(self, df: pd.DataFrame, predictions: list) -> str:
        """生成折线图，返回Base64字符串"""
        
    def create_cluster_scatter(self, df, labels, ...) -> str:
        """生成聚类散点图，返回Base64字符串"""
```

**🔑 关键交叉点**：
- 人三的模块**不直接调用**人二的代码
- 人三依赖人一的**模型文件**和人二的**配置文件**
- 所有返回值都是**纯数据**（dict/list/str），不包含Web相关逻辑

---

### 4️⃣ **人四：数据库持久化与前端交互**（双向依赖）

#### 负责文件
```
【数据库层】
database/db.py                ← 被 app.py 调用
database/models.py            ← 被 database/services.py 使用
database/services.py          ← 被 app.py 调用
database/config.py            ← 被 database/db.py 使用
database/__init__.py          ← 导出接口

【前端层】
templates/index.html          ← Flask渲染
static/js/main.js             ← 浏览器执行
static/css/style.css          ← 样式

【工具脚本】
init_db.py                    ← 独立运行，初始化数据库
```

#### 依赖关系

##### ✅ 数据库层依赖
```python
# database/db.py
from database.config import DatabaseConfig  # 同级模块
import pymysql                               # 第三方库
from sqlalchemy import create_engine         # 第三方库

# database/models.py
from database.db import Base  # 同级模块
from sqlalchemy import Column, Integer, ...  # 第三方库

# database/services.py
from database.models import PredictionRecord  # 同级模块
from sqlalchemy.orm import Session            # 第三方库
```

##### ✅ 前端层依赖
```html
<!-- templates/index.html -->
<!-- 依赖人二的Flask路由 -->
<form action="/predict" method="POST">  <!-- 人二的路由 -->
<script src="{{ url_for('static', filename='js/main.js') }}"></script>
```

```javascript
// static/js/main.js
// 依赖人二的API端点
fetch('/predict', {...})           // 人二的路由
fetch('/upload', {...})            // 人二的路由
fetch('/generate_chart', {...})    // 人二的路由
fetch('/cluster', {...})           // 人二的路由
fetch('/export', {...})            // 人二的路由
```

##### ✅ 被【人二】调用
```python
# app.py 中调用
from database import init_db, PredictionService  # 人四
from database.db import SessionLocal             # 人四

# 初始化
init_db()  # 创建表

# 保存记录
db = SessionLocal()
PredictionService.save_single_prediction(db, input_data, result)
PredictionService.save_batch_predictions(db, records, batch_id)
```

#### 对外提供的接口

##### 1. 数据库层接口（供人二调用）
```python
# database/__init__.py 导出
from database.db import get_db, init_db, close_db
from database.services import PredictionService

# 使用示例（人二的 app.py）
init_db()  # 初始化

db = SessionLocal()
try:
    PredictionService.save_single_prediction(db, data, result)
finally:
    db.close()
```

##### 2. 前端层接口（调用人二的API）
```javascript
// static/js/main.js 调用
POST /predict          → 单条预测
POST /upload           → 批量预测
POST /generate_chart   → 生成图表
POST /cluster          → 聚类分析
POST /export           → 导出CSV
```

**🔑 关键交叉点**：
- 数据库层：**被动调用**，被人二的 `app.py` 使用
- 前端层：**主动调用**，通过HTTP请求调用人二的API
- 人四是**唯一跨越前后端**的角色

---

## 🎯 交叉点详细分析

### 交叉点1：`app.py` ↔ `predictor.py`

**调用链**：
```
用户 → index.html (人四)
    → fetch('/predict') 
    → app.py (人二)
    → predictor.predict_single() (人三)
    → 返回JSON
    → 前端显示结果 (人四)
```

**接口契约**：
```python
# 人三保证
def predict_single(self, input_data: dict) -> dict:
    """
    必须返回：
    {
        'risk': float (0-1),
        'risk_percent': float (0-100)
    }
    """

# 人二保证
@app.route('/predict', methods=['POST'])
def predict():
    """
    必须返回：
    {
        'success': bool,
        'risk': float,
        'risk_percent': float,
        'level': str ('safe'/'warning'/'danger'),
        'suggestion': str,
        'message': str
    }
    """
```

**责任划分**：
- 人三：只负责**模型预测**，返回原始概率
- 人二：负责**业务逻辑**（风险分级、建议生成）+ **数据库保存**

---

### 交叉点2：`app.py` ↔ `data_processor.py`

**调用链**：
```
用户上传CSV 
    → index.html (人四)
    → fetch('/upload')
    → app.py (人二)
    → data_processor.load_file() (人三)
    → data_processor.clean_data() (人三)
    → data_processor.encode_categorical() (人三)
    → predictor.predict_batch() (人三)
    → 返回JSON
    → 前端显示表格 (人四)
```

**接口契约**：
```python
# 人三保证
def load_file(self, file, filename: str) -> pd.DataFrame:
    """支持CSV和Excel格式"""

def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
    """处理缺失值、异常值"""

def encode_categorical(self, df: pd.DataFrame) -> pd.DataFrame:
    """分类变量转数字"""
```

**责任划分**：
- 人三：负责**数据预处理**（清洗、编码）
- 人二：负责**流程编排** + **结果格式化**

---

### 交叉点3：`app.py` ↔ `PredictionService`

**调用链**：
```
预测完成
    → app.py (人二)
    → SessionLocal() (人四)
    → PredictionService.save_single_prediction() (人四)
    → 写入MySQL
    → 返回记录对象
```

**接口契约**：
```python
# 人四保证
@staticmethod
def save_single_prediction(db: Session, input_data: Dict, result: Dict) -> PredictionRecord:
    """
    参数：
    - db: 数据库会话
    - input_data: 用户输入 {gender, age, ...}
    - result: 预测结果 {risk, risk_percent, level, suggestion}
    
    返回：保存的记录对象
    """
```

**责任划分**：
- 人四：负责**数据库操作**（CRUD）
- 人二：负责**调用时机**（预测成功后立即保存）

---

### 交叉点4：`app.py` ↔ `visualizer.py`

**调用链**：
```
用户点击图表按钮
    → index.html (人四)
    → fetch('/generate_chart')
    → app.py (人二)
    → visualizer.create_histogram() (人三)
    → 返回Base64图片
    → 前端显示 <img> (人四)
```

**接口契约**：
```python
# 人三保证
def create_histogram(self, df: pd.DataFrame, column: str) -> str:
    """
    返回：Base64编码的PNG图片字符串
    例如："iVBORw0KGgoAAAANSUhEUgAA..."
    """
```

**责任划分**：
- 人三：负责**图表生成**（Matplotlib绘图）
- 人二：负责**数据准备**（解析CSV、预处理）
- 人四：负责**图片展示**（Base64转<img>标签）

---

### 交叉点5：`config.py` 被多方使用

**使用者**：
```python
# 人二使用
from config import Config
app.config.from_object(Config)

# 人三使用
from config import Config
with open(Config.MODEL_PATH, 'rb') as f: ...

# 人四不使用（有独立的 database/config.py）
```

**配置内容**：
```python
class Config:
    # 人二使用
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    
    # 人三使用
    MODEL_PATH = 'model/model.pkl'
    FEATURE_COLUMNS_PATH = 'model/feature_columns.pkl'
    GENDER_MAP = {'Male': 0, 'Female': 1, ...}
    HIGH_RISK_THRESHOLD = 0.5
    
    # 人四有自己的配置
    # database/config.py 中有 DatabaseConfig
```

**责任划分**：
- 人二：维护**全局配置**
- 人四：维护**数据库专用配置**

---

## 📋 接口汇总表

### 人二 → 人三（调用）

| 调用方 | 被调用方 | 方法 | 用途 |
|--------|---------|------|------|
| `app.py` | `StrokePredictor` | `predict_single()` | 单条预测 |
| `app.py` | `StrokePredictor` | `predict_batch()` | 批量预测 |
| `app.py` | `DataProcessor` | `load_file()` | 加载文件 |
| `app.py` | `DataProcessor` | `clean_data()` | 数据清洗 |
| `app.py` | `DataProcessor` | `encode_categorical()` | 编码分类变量 |
| `app.py` | `DataProcessor` | `prepare_input_data()` | 处理表单 |
| `app.py` | `DataProcessor` | `classify_risk()` | 风险分级 |
| `app.py` | `Visualizer` | `create_histogram()` | 直方图 |
| `app.py` | `Visualizer` | `create_boxplot()` | 箱线图 |
| `app.py` | `Visualizer` | `create_correlation_heatmap()` | 热力图 |
| `app.py` | `Visualizer` | `create_bar_chart()` | 条形图 |
| `app.py` | `Visualizer` | `create_pie_chart()` | 饼图 |
| `app.py` | `Visualizer` | `create_line_chart()` | 折线图 |
| `app.py` | `Visualizer` | `create_cluster_scatter()` | 聚类散点图 |
| `app.py` | `ClusterAnalyzer` | `fit_predict()` | 执行聚类 |

### 人二 → 人四（调用）

| 调用方 | 被调用方 | 方法 | 用途 |
|--------|---------|------|------|
| `app.py` | `init_db()` | - | 初始化数据库 |
| `app.py` | `SessionLocal()` | - | 获取数据库会话 |
| `app.py` | `PredictionService` | `save_single_prediction()` | 保存单次预测 |
| `app.py` | `PredictionService` | `save_batch_predictions()` | 保存批量预测 |

### 人四 → 人二（HTTP请求）

| 调用方 | 被调用方 | 端点 | 用途 |
|--------|---------|------|------|
| `main.js` | `app.py` | `POST /predict` | 单条预测 |
| `main.js` | `app.py` | `POST /upload` | 批量预测 |
| `main.js` | `app.py` | `POST /generate_chart` | 生成图表 |
| `main.js` | `app.py` | `POST /cluster` | 聚类分析 |
| `main.js` | `app.py` | `POST /export` | 导出CSV |

---

## 🚧 边界约定

### 1. 人三不应该做的事
- ❌ 不要直接操作数据库
- ❌ 不要处理HTTP请求/响应
- ❌ 不要渲染HTML
- ❌ 不要访问 `request` 对象

### 2. 人四不应该做的事
- ❌ 不要直接调用模型预测
- ❌ 不要处理数据清洗逻辑
- ❌ 不要生成图表（只负责展示）
- ❌ 不要修改 `config.py`（用 `database/config.py`）

### 3. 人二不应该做的事
- ❌ 不要直接写SQL语句
- ❌ 不要实现算法细节
- ❌ 不要在前端写业务逻辑
- ❌ 不要硬编码配置参数

### 4. 人一不应该做的事
- ❌ 不要涉及Web框架
- ❌ 不要调用API
- ❌ 不要操作数据库
- ❌ 不要处理前端代码

---

## 🔄 数据流转示例

### 示例1：单条预测完整流程

```
1. 【人四】用户填写表单 → main.js 收集数据
   FormData: {gender: "Male", age: "45", ...}

2. 【人四】发送请求
   fetch('/predict', {method: 'POST', body: formData})

3. 【人二】接收请求
   @app.route('/predict')
   input_data = request.form

4. 【人二】调用数据处理
   input_data = data_processor.prepare_input_data(input_data)
   # 转换为：{'gender': 0, 'age': 45.0, ...}

5. 【人三】执行预测
   result = predictor.predict_single(input_data)
   # 返回：{'risk': 0.65, 'risk_percent': 65.0}

6. 【人二】业务逻辑
   if risk >= 0.5:
       level = "danger"
       suggestion = "高风险！建议立即就医检查"

7. 【人二】保存到数据库
   db = SessionLocal()
   PredictionService.save_single_prediction(db, input_data, result)

8. 【人二】返回JSON
   return jsonify({
       'success': True,
       'risk': 0.65,
       'level': 'danger',
       'suggestion': '...',
       'message': '...'
   })

9. 【人四】前端渲染
   const data = await response.json()
   document.getElementById('predictResult').innerHTML = `
       <div class="risk-card ${data.level}">
           ...
       </div>
   `
```

---

## 📝 协作建议

### 1. 接口先行
在开发前，先约定好接口签名：
```python
# 人三和人二约定
def predict_single(input_data: dict) -> dict:
    # 输入格式、输出格式提前确定
```

### 2. Mock数据测试
```python
# 人二可以Mock人三的返回值，独立测试
mock_result = {'risk': 0.65, 'risk_percent': 65.0}
```

### 3. 版本控制
```bash
# 每人一个分支
git checkout -b person1-data
git checkout -b person2-backend
git checkout -b person3-ml
git checkout -b person4-frontend-db

# 定期合并到主分支
git merge person1-data
git merge person2-backend
...
```

### 4. 统一配置
```python
# 人二维护 config.py
# 人四维护 database/config.py
# 避免配置冲突
```

---

## ✅ 总结

### 交叉程度排序
1. **人二（后端）**：交叉最多，是集成中心
2. **人四（数据库+前端）**：双向交叉，跨越前后端
3. **人三（ML+服务）**：被调用方，依赖较少
4. **人一（数据+训练）**：最独立，只输出模型文件

### 关键原则
- **单向依赖**：下层不依赖上层
- **接口隔离**：通过函数签名解耦
- **职责单一**：每个模块只做一件事
- **配置分离**：全局配置 vs 数据库配置

这样分工虽然有交叉，但**边界清晰**，各自负责明确的模块！
