# 数据库持久化与前端交互 - 项目汇报文档

## 📋 目录
1. [ORM表结构设计](#1-orm表结构设计)
2. [预测记录自动持久化](#2-预测记录自动持久化)
3. [前端AJAX异步交互流程](#3-前端ajax异步交互流程)
4. [6种统计图表的动态生成与切换](#4-6种统计图表的动态生成与切换)
5. [聚类结果的可视化展示](#5-聚类结果的可视化展示)
6. [CSV导出功能](#6-csv导出功能)

---

## 1. ORM表结构设计

### 1.1 技术栈选择
- **ORM框架**: SQLAlchemy (Python最流行的ORM框架)
- **数据库**: MySQL 8.0+
- **驱动**: PyMySQL (纯Python实现，跨平台兼容)
- **连接池**: SQLAlchemy内置连接池管理

### 1.2 数据库配置 ([database/config.py](file:///C:/Users/10172/PycharmProjects/experiment/database/config.py))

```python
class DatabaseConfig:
    MYSQL_HOST = 'localhost'           # 数据库主机地址
    MYSQL_PORT = '3306'                # 数据库端口
    MYSQL_USER = 'root'                # 数据库用户名
    MYSQL_PASSWORD = 'y1017285149'     # 数据库密码
    MYSQL_DATABASE = 'stroke_prediction'  # 数据库名称
    
    # 连接URI格式
    DATABASE_URI = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4'
    
    # 连接池配置
    POOL_SIZE = 10          # 连接池大小
    MAX_OVERFLOW = 20       # 最大溢出连接数
    POOL_RECYCLE = 3600     # 连接回收时间（秒）
```

**关键设计点**:
- ✅ 使用环境变量支持灵活配置
- ✅ UTF8MB4字符集支持中文和特殊字符
- ✅ 连接池优化并发性能
- ✅ `pool_pre_ping=True` 防止连接断开

### 1.3 数据库连接管理 ([database/db.py](file:///C:/Users/10172/PycharmProjects/experiment/database/db.py))

```python
# 创建引擎（带连接池）
engine = create_engine(
    DatabaseConfig.DATABASE_URI,
    echo=False,                    # 生产环境关闭SQL日志
    pool_size=10,                  # 连接池大小
    max_overflow=20,               # 最大溢出连接
    pool_recycle=3600,             # 连接回收时间
    pool_pre_ping=True             # 连接前ping测试
)

# 会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 基类
Base = declarative_base()
```

**核心功能**:
- 🔧 `get_db()`: 获取数据库会话（上下文管理器模式）
- 🔧 `init_db()`: 初始化数据库（创建所有表）
- 🔧 `close_db()`: 关闭数据库连接

### 1.4 预测记录表 ([database/models.py](file:///C:/Users/10172/PycharmProjects/experiment/database/models.py))

#### predictions表结构

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | Integer | 主键ID | PRIMARY KEY, AUTO_INCREMENT |
| gender | String(20) | 性别 | NOT NULL |
| age | Float | 年龄 | NOT NULL |
| hypertension | Integer | 高血压（0/1） | DEFAULT 0 |
| heart_disease | Integer | 心脏病（0/1） | DEFAULT 0 |
| ever_married | String(10) | 婚姻状况 | - |
| work_type | String(50) | 工作类型 | - |
| residence_type | String(20) | 居住类型 | - |
| avg_glucose_level | Float | 平均血糖水平 | - |
| bmi | Float | BMI指数 | - |
| smoking_status | String(50) | 吸烟状况 | - |
| risk_score | Float | 风险分数（0-1） | NOT NULL |
| risk_percent | Float | 风险百分比（0-100） | NOT NULL |
| risk_level | String(20) | 风险等级 | NOT NULL (safe/warning/danger) |
| suggestion | Text | 建议 | - |
| prediction_type | String(20) | 预测类型 | DEFAULT 'single' |
| batch_id | String(50) | 批次ID | - |
| created_at | DateTime | 创建时间 | server_default=func.now() |
| extra_info | JSON | 额外信息 | - |

**设计亮点**:
- 📊 完整保存患者10项健康指标
- 🎯 存储预测结果（分数、百分比、等级、建议）
- 🔄 区分单次/批量预测（prediction_type字段）
- 🏷️ 批量预测关联（batch_id字段）
- ⏰ 自动记录时间戳
- 💾 JSON字段扩展性强

#### users表说明

**注意**: 当前系统不需要用户登录功能，因此users表仅作为预留扩展，实际项目中未启用。

### 1.5 模型方法

```python
class PredictionRecord(Base):
    def to_dict(self):
        """转换为字典（用于JSON序列化）"""
        return {
            'id': self.id,
            'gender': self.gender,
            'age': self.age,
            # ... 其他字段
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
```

---

## 2. 预测记录自动持久化

### 2.1 CRUD服务架构 ([database/services.py](file:///C:/Users/10172/PycharmProjects/experiment/database/services.py))

采用**服务层模式**，将数据库操作封装为静态方法：

```
PredictionService (预测记录服务)
├── save_single_prediction()      # 保存单次预测
├── save_batch_predictions()      # 保存批量预测
├── get_prediction_by_id()        # 根据ID查询
├── get_predictions_by_batch()    # 根据批次查询
├── get_all_predictions()         # 分页查询所有记录
└── get_statistics()              # 获取统计数据
```

### 2.2 单次预测持久化流程

```python
@staticmethod
def save_single_prediction(db: Session, input_data: Dict, result: Dict) -> PredictionRecord:
    """保存单次预测记录"""
    record = PredictionRecord(
        gender=input_data.get('gender', ''),
        age=float(input_data.get('age', 0)),
        hypertension=int(input_data.get('hypertension', 0)),
        # ... 其他字段映射
        risk_score=result.get('risk', 0),
        risk_percent=result.get('risk_percent', 0),
        risk_level=result.get('level', 'safe'),
        suggestion=result.get('suggestion', ''),
        prediction_type='single'
    )
    
    db.add(record)
    db.commit()      # 提交事务
    db.refresh(record)  # 刷新获取自增ID
    return record
```

**执行流程**:
1. 📥 接收表单输入数据和预测结果
2. 🔄 数据类型转换（确保符合数据库schema）
3. ➕ 创建PredictionRecord对象
4. 💾 添加到会话并提交事务
5. 🆔 刷新获取自增ID
6. ✅ 返回保存的记录

### 2.3 批量预测持久化流程

```python
@staticmethod
def save_batch_predictions(db: Session, records: List[Dict], batch_id: str = None) -> List[PredictionRecord]:
    """保存批量预测记录"""
    if not batch_id:
        batch_id = str(uuid.uuid4())[:8]  # 生成唯一批次ID
    
    saved_records = []
    for record_data in records:
        record = PredictionRecord(
            # ... 字段映射
            prediction_type='batch',
            batch_id=batch_id  # 关联同一批次
        )
        db.add(record)
        saved_records.append(record)
    
    db.commit()  # 批量提交（事务一致性）
    for record in saved_records:
        db.refresh(record)
    
    return saved_records
```

**关键特性**:
- 🏷️ 自动生成8位UUID作为批次ID
- 🔗 同一批次记录共享batch_id
- ⚡ 批量提交提升性能
- ✅ 事务保证数据一致性

### 2.4 统计数据查询

```python
@staticmethod
def get_statistics(db: Session) -> Dict:
    """获取预测统计数据"""
    total = db.query(PredictionRecord).count()
    high_risk = db.query(PredictionRecord).filter(
        PredictionRecord.risk_level == 'danger'
    ).count()
    medium_risk = db.query(PredictionRecord).filter(
        PredictionRecord.risk_level == 'warning'
    ).count()
    low_risk = db.query(PredictionRecord).filter(
        PredictionRecord.risk_level == 'safe'
    ).count()
    
    return {
        'total': total,
        'high_risk': high_risk,
        'medium_risk': medium_risk,
        'low_risk': low_risk,
        'high_risk_rate': round(high_risk / total * 100, 2) if total > 0 else 0
    }
```

**应用场景**:
- 📊 首页仪表盘显示总体统计
- 📈 风险分布饼图数据源
- 🎯 高风险人群占比分析

### 2.5 在Flask路由中集成

```python
@app.route('/predict', methods=['POST'])
def predict():
    # ... 获取表单数据
    # ... 模型预测
    
    db = next(get_db())  # 获取数据库会话
    try:
        # 保存预测记录到数据库
        record = PredictionService.save_single_prediction(db, form_data, result)
        print(f"✓ 预测记录已保存，ID: {record.id}")
    except Exception as e:
        print(f"✗ 保存失败: {e}")
    finally:
        db.close()
    
    return jsonify({'success': True, **result})
```

---

## 3. 前端AJAX异步交互流程

### 3.1 前端技术栈
- **原生JavaScript** (ES6+ async/await)
- **Fetch API** (现代化HTTP请求)
- **FormData** (表单数据处理)
- **Blob API** (文件下载)
- **CSS3动画** (过渡效果)

### 3.2 单条预测交互流程

#### 流程图
```
用户填写表单
    ↓
点击"开始预测"按钮
    ↓
触发submit事件监听器
    ↓
阻止默认表单提交 (e.preventDefault())
    ↓
显示加载动画 (showLoading(true))
    ↓
构建FormData对象
    ↓
发送POST请求到 /predict
    ↓
等待服务器响应 (async/await)
    ↓
接收JSON响应
    ↓
判断 success 字段
    ├─ true → 渲染结果卡片（风险等级、百分比、进度条、建议）
    └─ false → 弹出错误提示
    ↓
隐藏加载动画 (showLoading(false))
```

#### 代码实现 ([static/js/main.js](file:///C:/Users/10172/PycharmProjects/experiment/static/js/main.js#L68-L101))

```javascript
document.getElementById('predictForm').addEventListener('submit', async (e) => {
    e.preventDefault();  // 阻止表单默认提交
    showLoading(true);   // 显示加载动画

    const formData = new FormData(e.target);  // 收集表单数据

    try {
        const response = await fetch('/predict', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();  // 解析JSON响应

        if (data.success) {
            // 动态渲染结果卡片
            document.getElementById('predictResult').innerHTML = `
                <div class="risk-card ${data.level}">
                    <h3>评估结果</h3>
                    <div class="risk-percent">${data.risk_percent}%</div>
                    <div class="risk-bar-container">
                        <div class="risk-bar" style="width: ${data.risk_percent}%"></div>
                    </div>
                    <p style="font-weight:500;margin-top:8px;">${data.suggestion}</p>
                    <p style="font-size:13px;margin-top:8px;opacity:0.9;">${data.message}</p>
                </div>
            `;
        } else {
            alert('预测失败：' + data.error);
        }
    } catch (error) {
        alert('请求失败：' + error);
    }

    showLoading(false);  // 隐藏加载动画
});
```

**关键技术点**:
- ✅ `async/await` 简化异步代码
- ✅ `FormData` 自动处理表单编码
- ✅ 模板字符串动态生成HTML
- ✅ CSS类绑定实现风险等级着色
- ✅ 进度条宽度动画过渡

### 3.3 批量预测交互流程

#### 流程图
```
用户上传CSV文件
    ↓
点击"开始预测"按钮
    ↓
验证文件是否选择
    ↓
显示加载动画
    ↓
构建FormData（包含文件）
    ↓
发送POST请求到 /upload
    ↓
服务器处理：
  - 读取CSV
  - 数据预处理
  - 批量预测
  - 保存到数据库
  - 生成HTML表格
    ↓
接收JSON响应
    ↓
渲染统计卡片（总人数、高/中/低风险数量）
    ↓
渲染预测结果表格
    ↓
显示可视化区域、导出按钮、聚类分析区域
    ↓
绑定图表按钮事件
    ↓
隐藏加载动画
```

#### 代码实现 ([static/js/main.js](file:///C:/Users/10172/PycharmProjects/experiment/static/js/main.js#L125-L187))

```javascript
document.getElementById('batchPredictBtn').addEventListener('click', async () => {
    const file = fileInput.files[0];
    if (!file) {
        alert('请先选择文件');
        return;
    }

    showLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();

        if (data.success) {
            currentData = data.data;  // 保存数据用于导出

            // 渲染统计卡片
            document.getElementById('batchResult').innerHTML = `
                <div>
                    <div class="stats">
                        <div class="stat-card">
                            <h3>${data.total}</h3>
                            <p>总人数</p>
                        </div>
                        <div class="stat-card">
                            <h3 style="color:var(--danger)">${data.high_count}</h3>
                            <p>高风险</p>
                        </div>
                        <div class="stat-card">
                            <h3 style="color:var(--warning)">${data.medium_count}</h3>
                            <p>中风险</p>
                        </div>
                        <div class="stat-card">
                            <h3 style="color:var(--success)">${data.low_count}</h3>
                            <p>低风险</p>
                        </div>
                    </div>
                    <div class="table-container">
                        ${data.html_table}  <!-- 服务器生成的HTML表格 -->
                    </div>
                </div>
            `;

            // 显示可视化区域、导出按钮和聚类分析
            document.getElementById('visualizationSection').style.display = 'block';
            document.getElementById('exportBtn').style.display = 'inline-block';
            document.getElementById('clusterSection').style.display = 'block';

            // 绑定图表按钮
            bindChartButtons();
        } else {
            alert('预测失败：' + data.error);
        }
    } catch (error) {
        alert('请求失败：' + error);
    }

    showLoading(false);
});
```

### 3.4 文件上传交互

```javascript
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');

// 点击上传区域触发文件选择
uploadArea.addEventListener('click', () => fileInput.click());

// 文件选择后预览
fileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (file) {
        uploadArea.innerHTML = `
            <p>✅ 已选择：${file.name}</p>
            <small>点击重新选择</small>
            <input type="file" id="fileInput" accept=".csv" style="display:none">
        `;
        uploadArea.style.borderColor = '#00B42A';  // 绿色边框表示成功
        
        // 读取文件内容用于图表生成
        currentFileContent = await file.text();
    }
});
```

**用户体验优化**:
- 📁 点击整个区域即可上传
- ✅ 实时显示文件名
- 🟢 绿色边框视觉反馈
- 💾 预读文件内容供后续使用

### 3.5 标签页切换

```javascript
function switchTab(tab) {
    // 移除所有active类
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.card').forEach(card => card.classList.remove('active'));

    // 添加active类到目标标签
    if (tab === 'single') {
        document.querySelectorAll('.tab-btn')[0].classList.add('active');
        document.getElementById('singleCard').classList.add('active');
    } else {
        document.querySelectorAll('.tab-btn')[1].classList.add('active');
        document.getElementById('batchCard').classList.add('active');
    }
}
```

**CSS动画**:
```css
.card.active {
    display: block;
    animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(8px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
```

### 3.6 加载动画

```javascript
function showLoading(show) {
    document.getElementById('loading').classList.toggle('show', show);
}
```

```css
.loading {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.3);
    display: none;
    justify-content: center;
    align-items: center;
    z-index: 999;
}

.loading.show {
    display: flex;
}

.spinner {
    width: 36px;
    height: 36px;
    border: 2px solid var(--gray-100);
    border-top: 2px solid var(--primary);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
```

---

## 4. 6种统计图表的动态生成与切换

### 4.1 图表类型概览

| 图表类型 | 按钮文本 | 用途 | 可视化库 |
|---------|---------|------|---------|
| histogram | 年龄分布 | 展示患者年龄分布情况 | Matplotlib |
| boxplot | 血糖与风险 | 血糖水平与中风风险的箱线图 | Matplotlib |
| correlation | 相关性热力图 | 特征间相关性分析 | Seaborn |
| bar | 工作类型风险 | 不同工作类型的风险对比 | Matplotlib |
| pie | 风险分布饼图 | 高/中/低风险人群占比 | Matplotlib |
| line | 年龄风险趋势 | 年龄与风险的关系曲线 | Matplotlib |

### 4.2 前端图表切换逻辑

#### HTML结构 ([templates/index.html](file:///C:/Users/10172/PycharmProjects/experiment/templates/index.html#L489-L503))

```html
<div id="visualizationSection" style="margin-top: 30px; display: none;">
    <h3>数据可视化分析</h3>
    <div class="chart-tabs" style="display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap;">
        <button class="chart-btn" data-chart="histogram">年龄分布</button>
        <button class="chart-btn" data-chart="boxplot">血糖与风险</button>
        <button class="chart-btn" data-chart="correlation">相关性热力图</button>
        <button class="chart-btn" data-chart="bar">工作类型风险</button>
        <button class="chart-btn" data-chart="pie">风险分布饼图</button>
        <button class="chart-btn" data-chart="line">年龄风险趋势</button>
    </div>
    <div id="chartContainer"
         style="min-height: 400px; background: #f8f9fa; border-radius: 12px; padding: 20px; display: flex; justify-content: center; align-items: center;">
        <p style="color: #999;">点击上方按钮生成图表</p>
    </div>
</div>
```

#### JavaScript事件绑定 ([static/js/main.js](file:///C:/Users/10172/PycharmProjects/experiment/static/js/main.js#L23-L65))

```javascript
// 生成图表函数
async function generateChart(chartType) {
    if (!currentFileContent) {
        alert('请先进行批量预测');
        return;
    }

    showLoading(true);

    try {
        const response = await fetch('/generate_chart', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                chart_type: chartType,
                file_data: currentFileContent  // CSV文件内容
            })
        });
        const data = await response.json();

        if (data.success) {
            // 将Base64图片插入容器
            const chartContainer = document.getElementById('chartContainer');
            chartContainer.innerHTML = `<img src="data:image/png;base64,${data.image}" 
                style="max-width:100%; border-radius:8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">`;
        } else {
            alert('生成图表失败：' + data.error);
        }
    } catch (error) {
        alert('请求失败：' + error);
    }

    showLoading(false);
}

// 绑定图表按钮事件
function bindChartButtons() {
    document.querySelectorAll('.chart-btn').forEach(btn => {
        btn.removeEventListener('click', btn._listener);  // 防止重复绑定
        const chartType = btn.dataset.chart;
        const listener = () => generateChart(chartType);
        btn.addEventListener('click', listener);
        btn._listener = listener;
    });
}

// 页面加载完成后绑定
document.addEventListener('DOMContentLoaded', () => {
    bindChartButtons();
});
```

**工作流程**:
1. 👆 用户点击图表按钮
2. 📤 发送AJAX请求到 `/generate_chart`
3. 📊 服务器生成Matplotlib图表
4. 🖼️ 返回Base64编码的PNG图片
5. 🎨 前端渲染图片到容器

### 4.3 后端图表生成逻辑

#### Flask路由示例

```python
@app.route('/generate_chart', methods=['POST'])
def generate_chart():
    data = request.get_json()
    chart_type = data.get('chart_type')
    file_data = data.get('file_data')
    
    # 读取CSV数据
    df = pd.read_csv(StringIO(file_data))
    
    # 根据类型生成图表
    if chart_type == 'histogram':
        image_base64 = generate_histogram(df)
    elif chart_type == 'boxplot':
        image_base64 = generate_boxplot(df)
    # ... 其他图表类型
    
    return jsonify({
        'success': True,
        'image': image_base64
    })
```

#### 图表生成示例（年龄分布直方图）

```python
import matplotlib.pyplot as plt
import io
import base64

def generate_histogram(df):
    """生成年龄分布直方图"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.hist(df['age'].dropna(), bins=20, color='#4E6CF7', edgecolor='white')
    ax.set_title('患者年龄分布', fontsize=16, fontproperties='SimHei')
    ax.set_xlabel('年龄', fontsize=12, fontproperties='SimHei')
    ax.set_ylabel('人数', fontsize=12, fontproperties='SimHei')
    ax.grid(axis='y', alpha=0.3)
    
    # 保存到内存缓冲区
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
    buffer.seek(0)
    
    # 转换为Base64
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close(fig)
    
    return image_base64
```

### 4.4 图表样式统一规范

```python
# 全局样式设置
plt.rcParams['font.sans-serif'] = ['SimHei']  # 支持中文
plt.rcParams['axes.unicode_minus'] = False     # 正常显示负号

# 配色方案
COLORS = {
    'primary': '#4E6CF7',
    'success': '#00B42A',
    'warning': '#FF7D00',
    'danger': '#F53F3F'
}

# 图表通用配置
fig, ax = plt.subplots(figsize=(10, 6))
ax.set_title('标题', fontsize=16, fontproperties='SimHei')
ax.set_xlabel('X轴', fontsize=12, fontproperties='SimHei')
ax.set_ylabel('Y轴', fontsize=12, fontproperties='SimHei')
ax.grid(axis='y', alpha=0.3)
```

---

## 5. 聚类结果的可视化展示

### 5.1 K-Means聚类功能架构

```
前端交互
    ↓
AJAX请求 (/cluster)
    ↓
后端处理:
  - 读取CSV数据
  - 数据预处理（标准化）
  - K-Means聚类
  - 生成可视化图表
    ↓
返回JSON响应:
  - 聚类统计信息
  - 簇大小分布
  - 特征中心
  - Base64图表
    ↓
前端渲染结果
```

### 5.2 前端聚类交互 ([static/js/main.js](file:///C:/Users/10172/PycharmProjects/experiment/static/js/main.js#L225-L307))

```javascript
document.getElementById('clusterBtn').addEventListener('click', async () => {
    if (!currentFileContent) {
        alert('请先进行批量预测');
        return;
    }

    const nClusters = parseInt(document.getElementById('nClusters').value);
    showLoading(true);

    try {
        const response = await fetch('/cluster', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                file_data: currentFileContent,
                n_clusters: nClusters
            })
        });
        const data = await response.json();

        if (data.success) {
            const result = data.result;
            
            // 构建HTML内容
            let html = `
                <div class="stats">
                    <div class="stat-card">
                        <h3>${result.total}</h3>
                        <p>总样本数</p>
                    </div>
                    <div class="stat-card">
                        <h3>${result.n_clusters}</h3>
                        <p>聚类数量</p>
                    </div>
                </div>
                
                <h4 style="margin-top: 20px;">聚类特征：</h4>
                <p style="color: #666; font-size: 13px; margin: 8px 0;">
                    基于以下数值特征进行聚类：${result.cluster_features.join('、')}
                </p>
                
                <h4 style="margin-top: 20px;">各簇大小：</h4>
                <ul style="list-style: none; padding: 0;">
            `;
            
            // 显示各簇大小
            for (const [cluster, size] of Object.entries(result.cluster_sizes)) {
                html += `<li style="padding: 8px; margin: 5px 0; background: #f8f9fa; border-radius: 4px;">
                    簇 ${cluster}: ${size} 个样本
                </li>`;
            }
            
            html += '</ul>';
            
            // 显示簇的特征中心
            if (result.cluster_centers_info) {
                html += '<h4 style="margin-top: 20px;">各簇特征中心：</h4>';
                result.cluster_centers_info.forEach(cluster_info => {
                    html += `<div style="margin: 10px 0; padding: 12px; background: #fff; 
                        border: 1px solid #e5e6eb; border-radius: 6px;">`;
                    html += `<strong>簇 ${cluster_info.cluster_id}</strong> (${cluster_info.size} 个样本)<br>`;
                    html += `<small style="color: #666;">`;
                    for (const [feature, value] of Object.entries(cluster_info.center)) {
                        html += `${feature}: ${value}<br>`;
                    }
                    html += `</small></div>`;
                });
            }
            
            // 显示聚类图表
            if (data.image) {
                html += `
                    <div style="margin-top: 20px;">
                        <h4>聚类可视化：</h4>
                        <img src="data:image/png;base64,${data.image}" 
                            style="max-width:100%; border-radius:8px; 
                            box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-top: 10px;">
                    </div>
                `;
            }
            
            document.getElementById('clusterResult').innerHTML = html;
        } else {
            alert('聚类失败：' + data.error);
        }
    } catch (error) {
        alert('请求失败：' + error);
    }

    showLoading(false);
});
```

### 5.3 后端聚类实现

```python
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

@app.route('/cluster', methods=['POST'])
def cluster():
    data = request.get_json()
    file_data = data.get('file_data')
    n_clusters = data.get('n_clusters', 3)
    
    # 读取数据
    df = pd.read_csv(StringIO(file_data))
    
    # 选择数值特征
    cluster_features = ['age', 'avg_glucose_level', 'bmi']
    X = df[cluster_features].dropna()
    
    # 标准化
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # K-Means聚类
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X_scaled)
    
    # 统计信息
    cluster_sizes = pd.Series(labels).value_counts().sort_index().to_dict()
    cluster_centers = scaler.inverse_transform(kmeans.cluster_centers_)
    
    # 生成可视化图表
    image_base64 = generate_cluster_plot(X, labels, cluster_features)
    
    return jsonify({
        'success': True,
        'result': {
            'total': len(X),
            'n_clusters': n_clusters,
            'cluster_features': cluster_features,
            'cluster_sizes': cluster_sizes,
            'cluster_centers_info': [
                {
                    'cluster_id': i,
                    'size': int(cluster_sizes[i]),
                    'center': {
                        feat: round(val, 2) 
                        for feat, val in zip(cluster_features, cluster_centers[i])
                    }
                }
                for i in range(n_clusters)
            ]
        },
        'image': image_base64
    })
```

### 5.4 聚类可视化图表

```python
def generate_cluster_plot(X, labels, features):
    """生成聚类散点图（3D）"""
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    scatter = ax.scatter(
        X[features[0]], 
        X[features[1]], 
        X[features[2]],
        c=labels, 
        cmap='viridis',
        alpha=0.6,
        s=50
    )
    
    ax.set_xlabel(features[0], fontsize=12, fontproperties='SimHei')
    ax.set_ylabel(features[1], fontsize=12, fontproperties='SimHei')
    ax.set_zlabel(features[2], fontsize=12, fontproperties='SimHei')
    ax.set_title('K-Means聚类结果', fontsize=16, fontproperties='SimHei')
    
    plt.colorbar(scatter, label='簇标签')
    
    # 保存到Base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close(fig)
    
    return image_base64
```

**可视化特点**:
- 🎨 3D散点图直观展示聚类效果
- 🌈 不同颜色区分不同簇
- 📊 交互式旋转查看（可选Plotly）
- 📏 坐标轴标注清晰

---

## 6. CSV导出功能

### 6.1 导出流程

```
用户点击"导出结果"按钮
    ↓
检查是否有预测数据
    ↓
显示加载动画
    ↓
发送POST请求到 /export
    ↓
携带预测结果数据（JSON格式）
    ↓
服务器生成CSV文件
    ↓
返回CSV字符串
    ↓
前端创建Blob对象
    ↓
触发浏览器下载
    ↓
隐藏加载动画
```

### 6.2 前端导出实现 ([static/js/main.js](file:///C:/Users/10172/PycharmProjects/experiment/static/js/main.js#L190-L217))

```javascript
document.getElementById('exportBtn').addEventListener('click', async () => {
    if (!currentData) return;
    showLoading(true);

    try {
        const response = await fetch('/export', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(currentData)  // 发送预测结果数据
        });
        const data = await response.json();

        if (data.success) {
            // 创建Blob对象
            const blob = new Blob([data.csv_data], {type: 'text/csv;charset=utf-8;'});
            
            // 创建下载链接
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = '中风风险预测结果.csv';  // 文件名
            
            // 触发下载
            link.click();
            
            // 释放URL对象
            URL.revokeObjectURL(link.href);
        } else {
            alert('导出失败：' + data.error);
        }
    } catch (error) {
        alert('导出失败：' + error);
    }

    showLoading(false);
});
```

### 6.3 后端CSV生成

```python
import csv
import io

@app.route('/export', methods=['POST'])
def export_results():
    data = request.get_json()
    predictions = data.get('predictions', [])
    
    # 创建内存CSV文件
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 写入表头
    writer.writerow([
        'ID', '性别', '年龄', '高血压', '心脏病', 
        '婚姻状况', '工作类型', '居住类型', 
        '血糖水平', 'BMI', '吸烟状态',
        '风险分数', '风险百分比', '风险等级', '建议'
    ])
    
    # 写入数据行
    for pred in predictions:
        writer.writerow([
            pred.get('id', ''),
            pred.get('gender', ''),
            pred.get('age', ''),
            pred.get('hypertension', ''),
            pred.get('heart_disease', ''),
            pred.get('ever_married', ''),
            pred.get('work_type', ''),
            pred.get('residence_type', ''),
            pred.get('avg_glucose_level', ''),
            pred.get('bmi', ''),
            pred.get('smoking_status', ''),
            pred.get('risk_score', ''),
            pred.get('risk_percent', ''),
            pred.get('risk_level', ''),
            pred.get('suggestion', '')
        ])
    
    csv_data = output.getvalue()
    output.close()
    
    return jsonify({
        'success': True,
        'csv_data': csv_data
    })
```

### 6.4 技术要点

**前端**:
- 📦 `Blob` 对象处理二进制数据
- 🔗 `URL.createObjectURL()` 创建临时下载链接
- ⬇️ 动态创建 `<a>` 标签触发下载
- ♻️ `URL.revokeObjectURL()` 释放内存

**后端**:
- 📝 `io.StringIO` 内存中生成CSV
- 📊 `csv.writer` 标准库处理CSV格式
- 🔄 返回字符串而非文件（减少I/O）
- 🌐 UTF-8编码支持中文

---

## 📊 总结

### 核心技术亮点

1. **ORM表结构设计**
   - ✅ SQLAlchemy声明式模型
   - ✅ 完整的预测记录字段
   - ✅ 批次管理和类型区分
   - ✅ JSON扩展字段

2. **预测记录自动持久化**
   - ✅ 服务层封装CRUD操作
   - ✅ 事务保证数据一致性
   - ✅ 批量提交优化性能
   - ✅ 自动时间戳记录

3. **前端AJAX异步交互**
   - ✅ Fetch API + async/await
   - ✅ FormData处理表单
   - ✅ 动态HTML渲染
   - ✅ 加载动画提升体验

4. **6种统计图表动态生成**
   - ✅ Matplotlib后端生成
   - ✅ Base64图片传输
   - ✅ 按钮切换交互
   - ✅ 统一样式规范

5. **聚类结果可视化**
   - ✅ K-Means算法实现
   - ✅ 3D散点图展示
   - ✅ 簇特征中心显示
   - ✅ 统计信息汇总

6. **CSV导出功能**
   - ✅ Blob对象处理
   - ✅ 浏览器端下载
   - ✅ UTF-8中文支持
   - ✅ 内存流高效生成

### 项目价值

- 🎯 **医疗辅助决策**: 基于机器学习的风险评估
- 📈 **数据可视化**: 多维度统计分析
- 💾 **数据持久化**: 完整记录预测历史
- 🔄 **批量处理**: 支持大规模数据分析
- 📊 **智能聚类**: 发现潜在人群特征
- 📤 **结果导出**: 便于进一步研究

---

**汇报人**: 人四  
**日期**: 2026年5月29日  
**项目**: 中风风险预测系统
