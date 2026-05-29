# 数据库持久化与前端交互 - 详细技术实现文档

**汇报人：人四**  
**负责模块：数据库层 + 前端交互层**

---

## 📁 我的负责文件清单

| 文件路径 | 说明 | 核心技术 |
|---------|------|---------|
| `database/db.py` | 数据库连接与Session管理 | SQLAlchemy引擎、连接池 |
| `database/models.py` | ORM模型定义（predictions表） | SQLAlchemy声明式基类 |
| `database/services.py` | CRUD服务层 | 事务管理、批量操作 |
| `database/config.py` | 数据库配置 | 环境变量、URI构建 |
| `templates/index.html` | 主页面HTML结构 | HTML5表单、CSS布局 |
| `static/js/main.js` | 前端交互逻辑 | Fetch API、DOM操作 |
| `static/css/style.css` | 样式美化 | CSS3动画、响应式设计 |

---

## 🗄️ 第一部分：数据库持久化实现

### 1.1 数据库配置 (database/config.py)

#### 📌 核心代码解析
```python
class DatabaseConfig:
    # MySQL连接参数
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')      # 主机地址
    MYSQL_PORT = os.getenv('MYSQL_PORT', '3306')           # 端口号
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')           # 用户名
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '密码')   # 密码
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'stroke_prediction')  # 数据库名
    
    # 构建连接URI（关键！）
    DATABASE_URI = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4'
    
    # 连接池配置（性能优化）
    POOL_SIZE = 10          # 保持10个活跃连接
    MAX_OVERFLOW = 20       # 最多额外创建20个连接
    POOL_RECYCLE = 3600     # 1小时后回收空闲连接
```

#### 🔑 关键技术点
- **`mysql+pymysql://`**：使用PyMySQL驱动连接MySQL
- **`charset=utf8mb4`**：支持中文和emoji等特殊字符
- **连接池**：避免频繁创建/销毁连接，提升并发性能
- **环境变量**：通过`os.getenv()`读取，方便不同环境切换

---

### 1.2 数据库连接管理 (database/db.py)

#### 📌 核心代码逐行解释
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from database.config import DatabaseConfig

# ① 创建数据库引擎（连接池的核心）
engine = create_engine(
    DatabaseConfig.DATABASE_URI,    # 连接字符串
    echo=False,                      # 不打印SQL日志（生产环境）
    pool_size=10,                    # 连接池大小
    max_overflow=20,                 # 最大溢出连接数
    pool_recycle=3600,               # 连接回收时间（秒）
    pool_pre_ping=True               # 使用前先ping测试连接是否有效
)

# ② 创建会话工厂（用于生成数据库会话）
SessionLocal = sessionmaker(
    autocommit=False,    # 不自动提交（需要手动commit）
    autoflush=False,     # 不自动刷新
    bind=engine          # 绑定到上面创建的引擎
)

# ③ 创建ORM基类（所有模型都要继承它）
Base = declarative_base()
```

#### 🔧 三个核心函数

##### ✅ get_db() - 获取数据库会话
```python
def get_db():
    """获取数据库会话（生成器模式）"""
    db = SessionLocal()        # 创建一个新的会话
    try:
        yield db               # 返回给调用者使用
    finally:
        db.close()             # 使用后自动关闭，防止连接泄漏
```
**使用场景**：在Flask路由中获取数据库连接
```python
db = next(get_db())  # 获取会话
try:
    # 执行数据库操作
    PredictionService.save_single_prediction(db, data, result)
finally:
    db.close()  # 确保关闭
```

##### ✅ init_db() - 初始化数据库
```python
def init_db():
    """创建所有数据表"""
    from database import models  # 导入模型（注册表结构）
    Base.metadata.create_all(bind=engine)  # 根据模型创建表
    print("✓ MySQL数据库初始化成功！")
```
**工作原理**：
1. 导入`models.py`，让SQLAlchemy知道有哪些表
2. `create_all()`检查表是否存在，不存在则创建
3. 不会删除已有数据（安全）

##### ✅ close_db() - 关闭连接
```python
def close_db():
    """关闭数据库连接"""
    engine.dispose()  # 释放连接池中的所有连接
```

---

### 1.3 ORM模型设计 (database/models.py)

#### 📊 predictions表结构详解

```python
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.sql import func
from database.db import Base

class PredictionRecord(Base):
    """预测记录表"""
    __tablename__ = 'predictions'  # 表名
    
    # === 主键 ===
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # === 患者基本信息（10个特征）===
    gender = Column(String(20), nullable=False)           # 性别
    age = Column(Float, nullable=False)                   # 年龄
    hypertension = Column(Integer, default=0)             # 高血压（0/1）
    heart_disease = Column(Integer, default=0)            # 心脏病（0/1）
    ever_married = Column(String(10))                     # 婚姻状况
    work_type = Column(String(50))                        # 工作类型
    residence_type = Column(String(20))                   # 居住类型
    avg_glucose_level = Column(Float)                     # 平均血糖
    bmi = Column(Float)                                   # BMI指数
    smoking_status = Column(String(50))                   # 吸烟状况
    
    # === 预测结果（4个字段）===
    risk_score = Column(Float, nullable=False)            # 风险分数（0-1）
    risk_percent = Column(Float, nullable=False)          # 风险百分比（0-100）
    risk_level = Column(String(20), nullable=False)       # 风险等级（safe/warning/danger）
    suggestion = Column(Text)                             # 建议文本
    
    # === 元数据（3个字段）===
    prediction_type = Column(String(20), default='single')  # 预测类型
    batch_id = Column(String(50))                           # 批次ID
    created_at = Column(DateTime, server_default=func.now())  # 自动时间戳
    
    # === 扩展字段 ===
    extra_info = Column(JSON)  # JSON格式，可存储任意额外信息
```

#### 🔑 关键字段说明

| 字段类型 | 用途 | 示例 |
|---------|------|------|
| `Integer` | 整数 | 年龄、高血压标志 |
| `Float` | 浮点数 | 血糖、BMI、风险分数 |
| `String(n)` | 字符串（最大长度n） | 性别、工作类型 |
| `Text` | 长文本 | 建议内容 |
| `DateTime` | 日期时间 | 创建时间 |
| `JSON` | JSON对象 | 扩展信息（MySQL 5.7+支持） |

#### 💡 to_dict()方法 - 转换为字典
```python
def to_dict(self):
    """将ORM对象转换为Python字典（用于JSON序列化）"""
    return {
        'id': self.id,
        'gender': self.gender,
        'age': self.age,
        # ... 其他字段
        'created_at': self.created_at.isoformat() if self.created_at else None
    }
```
**作用**：数据库对象不能直接转JSON，需要先转为字典

---

### 1.4 CRUD服务层 (database/services.py)

#### 🎯 PredictionService类 - 5个核心方法

##### ① save_single_prediction() - 保存单次预测
```python
@staticmethod
def save_single_prediction(db: Session, input_data: Dict, result: Dict) -> PredictionRecord:
    """
    保存单次预测记录到数据库
    
    参数：
    - db: 数据库会话（由get_db()提供）
    - input_data: 用户输入的表单数据（字典）
    - result: 模型预测结果（字典）
    
    返回：
    - 保存后的记录对象（包含自增ID）
    """
    # 步骤1：创建PredictionRecord对象
    record = PredictionRecord(
        gender=input_data.get('gender', ''),              # 从表单获取性别
        age=float(input_data.get('age', 0)),              # 转换为浮点数
        hypertension=int(input_data.get('hypertension', 0)),  # 转换为整数
        heart_disease=int(input_data.get('heart_disease', 0)),
        ever_married=input_data.get('ever_married', ''),
        work_type=input_data.get('work_type', ''),
        residence_type=input_data.get('residence_type', ''),
        avg_glucose_level=float(input_data.get('avg_glucose_level', 0)) if input_data.get('avg_glucose_level') else None,
        bmi=float(input_data.get('bmi', 0)) if input_data.get('bmi') else None,
        smoking_status=input_data.get('smoking_status', ''),
        risk_score=result.get('risk', 0),                 # 从预测结果获取
        risk_percent=result.get('risk_percent', 0),
        risk_level=result.get('level', 'safe'),
        suggestion=result.get('suggestion', ''),
        prediction_type='single'                          # 标记为单次预测
    )
    
    # 步骤2：添加到会话
    db.add(record)
    
    # 步骤3：提交事务（真正写入数据库）
    db.commit()
    
    # 步骤4：刷新对象（获取数据库生成的自增ID）
    db.refresh(record)
    
    return record
```

**在app.py中的调用**：
```python
@app.route('/predict', methods=['POST'])
def predict():
    # ... 预测逻辑 ...
    
    db = SessionLocal()  # 获取数据库会话
    try:
        PredictionService.save_single_prediction(db, input_data, {
            'risk': risk,
            'risk_percent': risk_percent,
            'level': level,
            'suggestion': suggestion
        })
    except Exception as db_error:
        print(f"保存到数据库失败: {db_error}")
    finally:
        db.close()  # 确保关闭连接
```

##### ② save_batch_predictions() - 保存批量预测
```python
@staticmethod
def save_batch_predictions(db: Session, records: List[Dict], batch_id: str = None) -> List[PredictionRecord]:
    """
    保存批量预测记录（一次保存多条）
    
    参数：
    - db: 数据库会话
    - records: 预测结果列表（每个元素是一个字典）
    - batch_id: 批次ID（可选，自动生成）
    
    返回：
    - 保存后的记录列表
    """
    # 如果没有提供batch_id，生成一个唯一的8位ID
    if not batch_id:
        batch_id = str(uuid.uuid4())[:8]  # 例如："a3f5b2c1"
    
    saved_records = []
    
    # 遍历每条记录，创建ORM对象
    for record_data in records:
        record = PredictionRecord(
            # ... 字段映射（同上）...
            prediction_type='batch',  # 标记为批量预测
            batch_id=batch_id         # 关联同一批次
        )
        db.add(record)                # 添加到会话（但不提交）
        saved_records.append(record)
    
    # 一次性提交所有记录（事务保证原子性）
    db.commit()
    
    # 刷新所有对象获取ID
    for record in saved_records:
        db.refresh(record)
    
    return saved_records
```

**关键优势**：
- 🚀 **批量提交**：比逐条提交快10倍以上
- 🔒 **事务一致性**：要么全部成功，要么全部回滚
- 🏷️ **批次关联**：通过batch_id可以查询同一次上传的所有记录

##### ③ get_statistics() - 获取统计数据
```python
@staticmethod
def get_statistics(db: Session) -> Dict:
    """
    获取预测统计数据（用于仪表盘）
    
    返回：
    {
        'total': 1000,           # 总记录数
        'high_risk': 150,        # 高风险数量
        'medium_risk': 250,      # 中风险数量
        'low_risk': 600,         # 低风险数量
        'high_risk_rate': 15.0   # 高风险占比（%）
    }
    """
    # 查询总记录数
    total = db.query(PredictionRecord).count()
    
    # 查询各风险等级的数量（filter过滤）
    high_risk = db.query(PredictionRecord).filter(
        PredictionRecord.risk_level == 'danger'
    ).count()
    
    medium_risk = db.query(PredictionRecord).filter(
        PredictionRecord.risk_level == 'warning'
    ).count()
    
    low_risk = db.query(PredictionRecord).filter(
        PredictionRecord.risk_level == 'safe'
    ).count()
    
    # 计算高风险占比（避免除以0）
    high_risk_rate = round(high_risk / total * 100, 2) if total > 0 else 0
    
    return {
        'total': total,
        'high_risk': high_risk,
        'medium_risk': medium_risk,
        'low_risk': low_risk,
        'high_risk_rate': high_risk_rate
    }
```

**SQL等价语句**：
```sql
-- total
SELECT COUNT(*) FROM predictions;

-- high_risk
SELECT COUNT(*) FROM predictions WHERE risk_level = 'danger';
```

##### ④ get_prediction_by_id() - 根据ID查询
```python
@staticmethod
def get_prediction_by_id(db: Session, prediction_id: int) -> Optional[PredictionRecord]:
    """查询单条记录"""
    return db.query(PredictionRecord).filter(
        PredictionRecord.id == prediction_id
    ).first()  # 返回第一条或None
```

##### ⑤ get_all_predictions() - 分页查询
```python
@staticmethod
def get_all_predictions(db: Session, limit: int = 100, offset: int = 0) -> List[PredictionRecord]:
    """
    分页查询所有记录
    
    参数：
    - limit: 每页数量（默认100）
    - offset: 偏移量（第几页）
    
    示例：
    - 第1页：limit=100, offset=0
    - 第2页：limit=100, offset=100
    """
    return db.query(PredictionRecord)\
        .order_by(PredictionRecord.created_at.desc())\  # 按时间倒序
        .limit(limit)\
        .offset(offset)\
        .all()
```

---

### 1.5 数据库初始化脚本 (init_db.py)

#### 🔄 完整重建流程
```python
def drop_database():
    """删除旧数据库"""
    connection = pymysql.connect(
        host=DatabaseConfig.MYSQL_HOST,
        port=int(DatabaseConfig.MYSQL_PORT),
        user=DatabaseConfig.MYSQL_USER,
        password=DatabaseConfig.MYSQL_PASSWORD,
        charset='utf8mb4'
    )
    
    cursor = connection.cursor()
    cursor.execute(f"DROP DATABASE IF EXISTS `{DatabaseConfig.MYSQL_DATABASE}`")
    cursor.close()
    connection.close()


def create_database():
    """创建新数据库"""
    connection = pymysql.connect(...)  # 同上
    
    cursor = connection.cursor()
    cursor.execute(
        f"CREATE DATABASE IF NOT EXISTS `{DatabaseConfig.MYSQL_DATABASE}` "
        f"DEFAULT CHARACTER SET utf8mb4 "
        f"DEFAULT COLLATE utf8mb4_unicode_ci"
    )
    cursor.close()
    connection.close()


if __name__ == '__main__':
    # 交互式确认
    confirm = input("⚠️  此操作将删除原有数据库并重建！是否继续？(yes/no): ")
    
    if confirm != 'yes':
        print("✗ 操作已取消")
        exit(0)
    
    # 执行流程
    drop_database()      # 1. 删除旧库
    create_database()    # 2. 创建新库
    test_connection()    # 3. 测试连接
    init_db()            # 4. 创建表结构
```

**使用方法**：
```bash
python init_db.py
# 输入 yes 确认删除并重建
```

---

## 🌐 第二部分：前端交互实现（JavaScript小白必看）

### 2.1 前端技术栈概览

| 技术 | 用途 | 难度 |
|------|------|------|
| **Fetch API** | 发送HTTP请求（替代AJAX） | ⭐⭐ |
| **async/await** | 简化异步代码 | ⭐⭐⭐ |
| **FormData** | 处理表单数据 | ⭐⭐ |
| **DOM操作** | 动态更新页面内容 | ⭐⭐ |
| **Blob API** | 处理文件下载 | ⭐⭐⭐ |
| **CSS3动画** | 过渡效果 | ⭐⭐ |

---

### 2.2 单条预测功能详解

#### 📋 HTML表单结构 (templates/index.html)
```html
<!-- 表单容器 -->
<form id="predictForm">
    <div class="form-grid">
        <!-- 性别选择框 -->
        <div class="form-group">
            <label>性别 *</label>
            <select name="gender" required>
                <option value="Male">男</option>
                <option value="Female">女</option>
                <option value="Other">其他</option>
            </select>
        </div>

        <!-- 年龄输入框 -->
        <div class="form-group">
            <label>年龄 *</label>
            <input type="number" name="age" min="0" step="1" required placeholder="请输入年龄">
        </div>

        <!-- 其他字段... -->
    </div>

    <!-- 提交按钮 -->
    <div class="text-center">
        <button type="submit" class="btn">开始预测</button>
    </div>
</form>

<!-- 结果显示区域（初始为空） -->
<div id="predictResult"></div>
```

#### 💻 JavaScript处理逻辑 (static/js/main.js)

```javascript
// 监听表单提交事件
document.getElementById('predictForm').addEventListener('submit', async (e) => {
    // ① 阻止表单默认提交行为（防止页面刷新）
    e.preventDefault();
    
    // ② 显示加载动画
    showLoading(true);

    // ③ 收集表单数据
    const formData = new FormData(e.target);
    // FormData会自动收集表单中所有带name属性的字段
    // 例如：{gender: "Male", age: "45", hypertension: "0", ...}

    try {
        // ④ 发送POST请求到后端
        const response = await fetch('/predict', {
            method: 'POST',      // HTTP方法
            body: formData       // 请求体（表单数据）
        });
        
        // ⑤ 解析JSON响应
        const data = await response.json();
        // data结构：{success: true, risk: 0.65, risk_percent: 65.0, level: "danger", suggestion: "..."}

        // ⑥ 判断是否成功
        if (data.success) {
            // ⑦ 动态生成HTML并插入页面
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
            
            // 注意：${data.level} 会是 "danger"/"warning"/"safe"
            // 对应CSS类：risk-card danger → 红色背景
        } else {
            // ⑧ 显示错误提示
            alert('预测失败：' + data.error);
        }
    } catch (error) {
        // ⑨ 捕获网络错误
        alert('请求失败：' + error);
    }

    // ⑩ 隐藏加载动画
    showLoading(false);
});
```

#### 🔍 逐行解释关键点

**Q1: 什么是 `async/await`？**
```javascript
// 传统写法（回调地狱）
fetch('/predict').then(response => {
    return response.json();
}).then(data => {
    console.log(data);
});

// async/await写法（同步风格）
const response = await fetch('/predict');
const data = await response.json();
console.log(data);
```
**优势**：代码更清晰，易于理解和维护

**Q2: `FormData` 是什么？**
```javascript
// 假设表单中有这些字段：
// <input name="gender" value="Male">
// <input name="age" value="45">

const formData = new FormData(formElement);

// FormData内部结构：
// {
//     gender: "Male",
//     age: "45",
//     hypertension: "0",
//     ...
// }

// 可以直接传给fetch，会自动编码为multipart/form-data
```

**Q3: 模板字符串 `` `...${变量}...` `` 是什么？**
```javascript
const name = "张三";
const age = 25;

// 传统拼接
const msg1 = "姓名：" + name + "，年龄：" + age;

// 模板字符串（更简洁）
const msg2 = `姓名：${name}，年龄：${age}`;

// 支持多行
const html = `
    <div>
        <h3>${name}</h3>
        <p>年龄：${age}</p>
    </div>
`;
```

**Q4: `innerHTML` 的作用？**
```javascript
// 假设HTML中有：<div id="result"></div>

// 动态插入HTML内容
document.getElementById('result').innerHTML = '<p>Hello World</p>';

// 结果：
// <div id="result"><p>Hello World</p></div>
```

---

### 2.3 批量预测功能详解

#### 📤 文件上传交互

**HTML结构**：
```html
<!-- 上传区域（点击触发文件选择） -->
<div class="upload-area" id="uploadArea">
    <p>点击或拖拽上传 CSV 文件</p>
    <small>支持格式：.csv 标准数据集</small>
    <!-- 隐藏的文件输入框 -->
    <input type="file" id="fileInput" accept=".csv" style="display:none">
</div>

<!-- 预测按钮 -->
<button id="batchPredictBtn" class="btn">开始预测</button>

<!-- 结果显示区 -->
<div id="batchResult"></div>

<!-- 可视化区域（初始隐藏） -->
<div id="visualizationSection" style="display: none;">
    <h3>数据可视化分析</h3>
    <div class="chart-tabs">
        <button class="chart-btn" data-chart="histogram">年龄分布</button>
        <button class="chart-btn" data-chart="boxplot">血糖与风险</button>
        <!-- 其他图表按钮... -->
    </div>
    <div id="chartContainer">
        <p style="color: #999;">点击上方按钮生成图表</p>
    </div>
</div>

<!-- 导出按钮（初始隐藏） -->
<button id="exportBtn" class="btn btn-secondary" style="display:none;">导出结果</button>

<!-- 聚类分析区域（初始隐藏） -->
<div id="clusterSection" style="display: none;">
    <h3>K-Means 聚类分析</h3>
    <label for="nClusters">聚类数量：</label>
    <input type="number" id="nClusters" value="3" min="2" max="10">
    <button id="clusterBtn" class="btn">开始聚类</button>
    <div id="clusterResult"></div>
</div>
```

**JavaScript逻辑**：
```javascript
// ========== 文件上传交互 ==========
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
let currentFileContent = null;  // 存储文件内容（用于图表生成）

// 点击上传区域 → 触发文件选择
uploadArea.addEventListener('click', () => fileInput.click());

// 文件选择后 → 预览文件名
fileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];  // 获取选择的文件
    if (file) {
        // 更新上传区域显示
        uploadArea.innerHTML = `
            <p>✅ 已选择：${file.name}</p>
            <small>点击重新选择</small>
            <input type="file" id="fileInput" accept=".csv" style="display:none">
        `;
        uploadArea.style.borderColor = '#00B42A';  // 绿色边框
        
        // 读取文件内容（用于后续图表生成）
        currentFileContent = await file.text();
        // file.text() 返回 Promise，需要 await
    }
});


// ========== 批量预测 ==========
document.getElementById('batchPredictBtn').addEventListener('click', async () => {
    const file = fileInput.files[0];
    
    // 验证是否选择了文件
    if (!file) {
        alert('请先选择文件');
        return;
    }

    showLoading(true);
    
    // 构建FormData（包含文件）
    const formData = new FormData();
    formData.append('file', file);  // 'file'是后端接收的字段名

    try {
        // 发送到 /upload 接口
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        // data结构：
        // {
        //     success: true,
        //     total: 500,
        //     high_count: 50,
        //     medium_count: 150,
        //     low_count: 300,
        //     html_table: "<table>...</table>",
        //     data: [...]  // 原始数据（用于导出）
        // }

        if (data.success) {
            // 保存数据（用于导出）
            currentData = data.data;

            // 渲染统计卡片 + 表格
            document.getElementById('batchResult').innerHTML = `
                <div>
                    <!-- 统计卡片 -->
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
                    
                    <!-- 数据表格 -->
                    <div class="table-container">
                        ${data.html_table}  <!-- 后端生成的HTML表格 -->
                    </div>
                </div>
            `;

            // 显示隐藏的区域
            document.getElementById('visualizationSection').style.display = 'block';
            document.getElementById('exportBtn').style.display = 'inline-block';
            document.getElementById('clusterSection').style.display = 'block';

            // 绑定图表按钮事件
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

---

### 2.4 图表切换功能详解

#### 🎨 6种图表类型

| 图表类型 | 按钮文本 | 用途 |
|---------|---------|------|
| histogram | 年龄分布 | 展示患者年龄分布情况 |
| boxplot | 血糖与风险 | 血糖水平与中风风险的箱线图 |
| correlation | 相关性热力图 | 特征间相关性分析 |
| bar | 工作类型风险 | 不同工作类型的风险对比 |
| pie | 风险分布饼图 | 高/中/低风险人群占比 |
| line | 年龄风险趋势 | 年龄与风险的关系曲线 |

#### 💻 实现逻辑

```javascript
// ========== 图表生成函数 ==========
async function generateChart(chartType) {
    // 验证是否有数据
    if (!currentFileContent) {
        alert('请先进行批量预测');
        return;
    }

    showLoading(true);

    try {
        // 发送请求到 /generate_chart
        const response = await fetch('/generate_chart', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},  // 指定JSON格式
            body: JSON.stringify({
                chart_type: chartType,      // 图表类型（如"histogram"）
                file_data: currentFileContent  // CSV文件内容
            })
        });
        
        const data = await response.json();
        // data结构：{success: true, image: "base64编码的图片字符串"}

        if (data.success) {
            // 将Base64图片插入容器
            const chartContainer = document.getElementById('chartContainer');
            chartContainer.innerHTML = `
                <img src="data:image/png;base64,${data.image}" 
                     style="max-width:100%; border-radius:8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            `;
            // data:image/png;base64, 是Base64图片的URL格式
        } else {
            alert('生成图表失败：' + data.error);
        }
    } catch (error) {
        alert('请求失败：' + error);
    }

    showLoading(false);
}


// ========== 绑定图表按钮事件 ==========
function bindChartButtons() {
    // 获取所有图表按钮
    document.querySelectorAll('.chart-btn').forEach(btn => {
        // 移除旧的事件监听器（防止重复绑定）
        btn.removeEventListener('click', btn._listener);
        
        // 获取图表类型（从data-chart属性）
        const chartType = btn.dataset.chart;
        // 例如：<button data-chart="histogram"> → chartType = "histogram"
        
        // 创建新的事件监听器
        const listener = () => generateChart(chartType);
        
        // 绑定点击事件
        btn.addEventListener('click', listener);
        
        // 保存监听器引用（用于后续移除）
        btn._listener = listener;
    });
}

// 页面加载完成后绑定
document.addEventListener('DOMContentLoaded', () => {
    bindChartButtons();
});
```

#### 🔍 关键技术点

**Q1: 什么是 `data-*` 属性？**
```html
<!-- HTML5自定义数据属性 -->
<button data-chart="histogram">年龄分布</button>
<button data-chart="boxplot">血糖与风险</button>

<!-- JavaScript中访问 -->
btn.dataset.chart  // 返回 "histogram" 或 "boxplot"
```

**Q2: Base64图片是什么？**
```javascript
// 传统图片URL
<img src="/images/chart.png">

// Base64图片URL（图片内容直接嵌入HTML）
<img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...">

// 优势：不需要额外的HTTP请求
// 劣势：HTML体积变大
```

**Q3: `querySelectorAll` 是什么？**
```javascript
// 获取所有匹配的元素（返回 NodeList）
const buttons = document.querySelectorAll('.chart-btn');

// 遍历
buttons.forEach(btn => {
    console.log(btn.textContent);  // 按钮文本
});
```

---

### 2.5 聚类分析功能详解

```javascript
// ========== 聚类分析 ==========
document.getElementById('clusterBtn').addEventListener('click', async () => {
    // 验证是否有数据
    if (!currentFileContent) {
        alert('请先进行批量预测');
        return;
    }

    // 获取用户设定的聚类数量
    const nClusters = parseInt(document.getElementById('nClusters').value);
    // parseInt("3") → 3（字符串转整数）
    
    showLoading(true);

    try {
        // 发送到 /cluster 接口
        const response = await fetch('/cluster', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                file_data: currentFileContent,
                n_clusters: nClusters
            })
        });
        
        const data = await response.json();
        // data结构：
        // {
        //     success: true,
        //     result: {
        //         total: 500,
        //         n_clusters: 3,
        //         cluster_features: ["年龄", "血糖", "BMI"],
        //         cluster_sizes: {"0": 200, "1": 180, "2": 120},
        //         cluster_centers_info: [
        //             {cluster_id: 0, size: 200, center: {年龄: 35.2, 血糖: 85.6, BMI: 24.1}},
        //             ...
        //         ]
        //     },
        //     image: "base64图片"
        // }

        if (data.success) {
            const result = data.result;
            
            // 构建HTML内容
            let html = `
                <!-- 统计卡片 -->
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
                
                <!-- 聚类特征说明 -->
                <h4 style="margin-top: 20px;">聚类特征：</h4>
                <p style="color: #666; font-size: 13px; margin: 8px 0;">
                    基于以下数值特征进行聚类：${result.cluster_features.join('、')}
                </p>
                // join('、') 将数组转为字符串：["年龄", "血糖"] → "年龄、血糖"
                
                <!-- 各簇大小 -->
                <h4 style="margin-top: 20px;">各簇大小：</h4>
                <ul style="list-style: none; padding: 0;">
            `;
            
            // 遍历各簇大小
            for (const [cluster, size] of Object.entries(result.cluster_sizes)) {
                // Object.entries({"0": 200, "1": 180}) → [["0", 200], ["1", 180]]
                html += `<li style="padding: 8px; margin: 5px 0; background: #f8f9fa; border-radius: 4px;">
                    簇 ${cluster}: ${size} 个样本
                </li>`;
            }
            
            html += '</ul>';
            
            // 显示簇的特征中心
            if (result.cluster_centers_info) {
                html += '<h4 style="margin-top: 20px;">各簇特征中心：</h4>';
                
                result.cluster_centers_info.forEach(cluster_info => {
                    html += `
                        <div style="margin: 10px 0; padding: 12px; background: #fff; 
                            border: 1px solid #e5e6eb; border-radius: 6px;">
                            <strong>簇 ${cluster_info.cluster_id}</strong> 
                            (${cluster_info.size} 个样本)<br>
                            <small style="color: #666;">
                    `;
                    
                    // 遍历特征中心的每个特征
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
            
            // 插入页面
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

---

### 2.6 CSV导出功能详解

```javascript
// ========== 导出结果 ==========
document.getElementById('exportBtn').addEventListener('click', async () => {
    // 验证是否有数据
    if (!currentData) return;
    
    showLoading(true);

    try {
        // 发送到 /export 接口
        const response = await fetch('/export', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(currentData)  // 发送预测结果数据
        });
        
        const data = await response.json();
        // data结构：{success: true, csv_data: "CSV格式的字符串"}

        if (data.success) {
            // ① 创建Blob对象（二进制大对象）
            const blob = new Blob([data.csv_data], {
                type: 'text/csv;charset=utf-8;'
            });
            // Blob是一个不可变的原始数据对象
            
            // ② 创建临时下载链接
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            // URL.createObjectURL() 创建一个指向Blob的临时URL
            // 例如：blob:http://localhost:8888/12345678-1234-1234-1234-123456789abc
            
            link.download = '中风风险预测结果.csv';  // 设置文件名
            
            // ③ 触发下载
            link.click();
            
            // ④ 释放URL对象（释放内存）
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

#### 🔍 Blob API 详解

```javascript
// 什么是Blob？
// Blob（Binary Large Object）是不可变的原始数据对象

// 创建Blob
const blob = new Blob(["Hello World"], {type: 'text/plain'});

// 常见MIME类型
'text/csv'          // CSV文件
'text/html'         // HTML文件
'application/pdf'   // PDF文件
'image/png'         // PNG图片

// URL.createObjectURL()
// 创建一个指向Blob的临时URL
const url = URL.createObjectURL(blob);
// url = "blob:http://example.com/12345..."

// 使用后必须释放
URL.revokeObjectURL(url);
```

---

### 2.7 通用工具函数

#### 🔄 加载动画
```javascript
function showLoading(show) {
    // show=true → 添加'show'类 → 显示加载动画
    // show=false → 移除'show'类 → 隐藏加载动画
    document.getElementById('loading').classList.toggle('show', show);
}
```

**CSS实现**：
```css
.loading {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.3);  /* 半透明黑色遮罩 */
    display: none;                     /* 默认隐藏 */
    justify-content: center;
    align-items: center;
    z-index: 999;                      /* 在最上层 */
}

.loading.show {
    display: flex;                     /* 显示时变为flex布局 */
}

.spinner {
    width: 36px;
    height: 36px;
    border: 2px solid var(--gray-100);
    border-top: 2px solid var(--primary);  /* 顶部颜色不同 */
    border-radius: 50%;                  /* 圆形 */
    animation: spin 0.8s linear infinite; /* 旋转动画 */
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
```

#### 📑 标签页切换
```javascript
function switchTab(tab) {
    // ① 移除所有active类
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.card').forEach(card => card.classList.remove('active'));

    // ② 激活目标标签
    if (tab === 'single') {
        document.querySelectorAll('.tab-btn')[0].classList.add('active');
        document.getElementById('singleCard').classList.add('active');
    } else {
        document.querySelectorAll('.tab-btn')[1].classList.add('active');
        document.getElementById('batchCard').classList.add('active');
    }
}
```

**CSS动画**：
```css
.card.active {
    display: block;
    animation: fadeIn 0.3s ease;  /* 淡入动画 */
}

@keyframes fadeIn {
    from {
        opacity: 0;                /* 完全透明 */
        transform: translateY(8px); /* 向下偏移8px */
    }
    to {
        opacity: 1;                /* 完全不透明 */
        transform: translateY(0);   /* 回到原位 */
    }
}
```

---

## 🎯 第三部分：前后端交互流程

### 3.1 单条预测完整流程

```
┌─────────────┐
│  用户填写表单  │
└──────┬──────┘
       │ 点击"开始预测"
       ↓
┌─────────────────────────────────┐
│  JavaScript (main.js)           │
│  1. 阻止表单默认提交             │
│  2. 收集表单数据 (FormData)      │
│  3. 显示加载动画                 │
│  4. 发送 POST /predict          │
└──────┬──────────────────────────┘
       │ Fetch API
       ↓
┌─────────────────────────────────┐
│  Flask (app.py)                 │
│  @app.route('/predict')         │
│  1. 接收表单数据                 │
│  2. 数据预处理                   │
│  3. 调用模型预测                 │
│  4. 保存到数据库                 │
│  5. 返回JSON响应                 │
└──────┬──────────────────────────┘
       │ jsonify({'success': True, ...})
       ↓
┌─────────────────────────────────┐
│  JavaScript (main.js)           │
│  1. 解析JSON响应                 │
│  2. 动态生成HTML                 │
│  3. 插入到 predictResult 区域    │
│  4. 隐藏加载动画                 │
└──────┬──────────────────────────┘
       │ DOM操作
       ↓
┌─────────────┐
│  用户看到结果  │
└─────────────┘
```

### 3.2 批量预测完整流程

```
┌─────────────┐
│  用户上传CSV  │
└──────┬──────┘
       │ 点击"开始预测"
       ↓
┌─────────────────────────────────┐
│  JavaScript (main.js)           │
│  1. 验证文件是否选择             │
│  2. 构建FormData (包含文件)      │
│  3. 发送 POST /upload           │
└──────┬──────────────────────────┘
       │ Fetch API
       ↓
┌─────────────────────────────────┐
│  Flask (app.py)                 │
│  @app.route('/upload')          │
│  1. 读取CSV文件                  │
│  2. 数据清洗 + 编码              │
│  3. 批量预测                     │
│  4. 保存到数据库 (批量)          │
│  5. 生成HTML表格                 │
│  6. 返回JSON (统计数据+表格)     │
└──────┬──────────────────────────┘
       │ jsonify({...})
       ↓
┌─────────────────────────────────┐
│  JavaScript (main.js)           │
│  1. 渲染统计卡片                 │
│  2. 渲染数据表格                 │
│  3. 显示可视化区域               │
│  4. 显示导出按钮                 │
│  5. 显示聚类分析区域             │
│  6. 绑定图表按钮事件             │
└──────┬──────────────────────────┘
       ↓
┌─────────────┐
│  用户看到结果  │
└─────────────┘
```

### 3.3 图表生成流程

```
┌─────────────┐
│ 用户点击图表按钮│
└──────┬──────┘
       │ 例如："年龄分布"
       ↓
┌─────────────────────────────────┐
│  JavaScript (main.js)           │
│  1. 获取 chart_type="histogram" │
│  2. 读取 currentFileContent     │
│  3. 发送 POST /generate_chart   │
│     {chart_type, file_data}     │
└──────┬──────────────────────────┘
       │ Fetch API
       ↓
┌─────────────────────────────────┐
│  Flask (app.py)                 │
│  @app.route('/generate_chart')  │
│  1. 解析CSV数据                  │
│  2. 数据清洗 + 编码              │
│  3. 调用 Visualizer 生成图表     │
│  4. Matplotlib绘制图形           │
│  5. 转为Base64编码               │
│  6. 返回JSON {image: base64}    │
└──────┬──────────────────────────┘
       │ jsonify({...})
       ↓
┌─────────────────────────────────┐
│  JavaScript (main.js)           │
│  1. 解析Base64图片              │
│  2. 创建 <img> 标签             │
│  3. 插入到 chartContainer       │
└──────┬──────────────────────────┘
       ↓
┌─────────────┐
│  用户看到图表  │
└─────────────┘
```

---

## 📊 第四部分：数据库表结构设计

### 4.1 predictions表ER图

```
┌─────────────────────────────────────────────┐
│              predictions 表                  │
├─────────────────────────────────────────────┤
│ 主键：                                       │
│   • id (INT, AUTO_INCREMENT)                │
├─────────────────────────────────────────────┤
│ 患者特征（10个字段）：                        │
│   • gender (VARCHAR 20)                     │
│   • age (FLOAT)                             │
│   • hypertension (INT, 0/1)                 │
│   • heart_disease (INT, 0/1)                │
│   • ever_married (VARCHAR 10)               │
│   • work_type (VARCHAR 50)                  │
│   • residence_type (VARCHAR 20)             │
│   • avg_glucose_level (FLOAT)               │
│   • bmi (FLOAT)                             │
│   • smoking_status (VARCHAR 50)             │
├─────────────────────────────────────────────┤
│ 预测结果（4个字段）：                         │
│   • risk_score (FLOAT, 0-1)                 │
│   • risk_percent (FLOAT, 0-100)             │
│   • risk_level (VARCHAR 20)                 │
│     值域：safe / warning / danger           │
│   • suggestion (TEXT)                       │
├─────────────────────────────────────────────┤
│ 元数据（3个字段）：                           │
│   • prediction_type (VARCHAR 20)            │
│     值域：single / batch                    │
│   • batch_id (VARCHAR 50)                   │
│     用于关联同一次批量预测的记录              │
│   • created_at (DATETIME)                   │
│     自动生成，记录创建时间                    │
├─────────────────────────────────────────────┤
│ 扩展字段：                                   │
│   • extra_info (JSON)                       │
│     可存储任意额外信息                        │
└─────────────────────────────────────────────┘
```

### 4.2 索引优化建议

```sql
-- 常用查询字段建议添加索引

-- 1. 按时间查询（最新记录）
CREATE INDEX idx_created_at ON predictions(created_at DESC);

-- 2. 按风险等级筛选
CREATE INDEX idx_risk_level ON predictions(risk_level);

-- 3. 按批次查询
CREATE INDEX idx_batch_id ON predictions(batch_id);

-- 4. 复合索引（组合查询）
CREATE INDEX idx_risk_time ON predictions(risk_level, created_at DESC);
```

---

## 🎓 第五部分：学习要点总结

### 5.1 数据库知识点

| 概念 | 说明 | 应用场景 |
|------|------|---------|
| **ORM** | 对象关系映射，用Python类操作数据库 | 避免写SQL语句 |
| **Session** | 数据库会话，管理事务 | 增删改查操作 |
| **连接池** | 复用数据库连接，提升性能 | 高并发场景 |
| **事务** | 一组操作要么全成功，要么全失败 | 批量保存数据 |
| **索引** | 加速查询的数据结构 | 频繁查询的字段 |

### 5.2 JavaScript知识点

| 概念 | 说明 | 示例 |
|------|------|------|
| **async/await** | 简化异步代码 | `const data = await fetch(...)` |
| **Fetch API** | 发送HTTP请求 | `fetch('/api', {method: 'POST'})` |
| **FormData** | 处理表单数据 | `new FormData(form)` |
| **模板字符串** | 动态生成HTML | `` `<div>${name}</div>` `` |
| **DOM操作** | 修改页面内容 | `element.innerHTML = '...'` |
| **Blob API** | 处理文件下载 | `new Blob([data])` |
| **事件监听** | 响应用户操作 | `addEventListener('click', fn)` |

### 5.3 前后端交互知识点

| 概念 | 说明 | 示例 |
|------|------|------|
| **RESTful API** | 统一的接口规范 | GET查询、POST创建 |
| **JSON** | 数据交换格式 | `{"success": true}` |
| **Base64** | 图片编码方式 | `data:image/png;base64,...` |
| **CORS** | 跨域资源共享 | 前后端分离时需要配置 |
| **AJAX** | 异步请求，不刷新页面 | Fetch API实现 |

---

## 💡 第六部分：常见问题解答

### Q1: 为什么要用ORM而不是直接写SQL？

**A:** 
```python
# ❌ 原生SQL（容易出错，不安全）
cursor.execute(f"INSERT INTO predictions VALUES ({age}, '{gender}')")

# ✅ ORM（类型安全，防SQL注入）
record = PredictionRecord(age=age, gender=gender)
db.add(record)
db.commit()
```

**优势**：
- 🔒 防止SQL注入攻击
- 📝 代码更易读和维护
- 🔄 数据库迁移更方便
- ✨ IDE智能提示

### Q2: 为什么前端要用async/await？

**A:** 
```javascript
// ❌ 回调地狱（难以阅读）
fetch('/predict')
  .then(response => response.json())
  .then(data => {
      console.log(data);
  })
  .catch(error => {
      console.error(error);
  });

// ✅ async/await（同步风格）
try {
    const response = await fetch('/predict');
    const data = await response.json();
    console.log(data);
} catch (error) {
    console.error(error);
}
```

### Q3: 为什么要用连接池？

**A:** 
- **没有连接池**：每次请求都创建新连接 → 慢（~100ms）
- **有连接池**：复用已有连接 → 快（~1ms）

**类比**：
- 没有连接池 = 每次喝水都去买新瓶子
- 有连接池 = 准备10个水杯，轮流使用

### Q4: Base64图片有什么优缺点？

**A:**
- ✅ **优点**：不需要额外的HTTP请求，加载更快
- ❌ **缺点**：图片体积增加33%，HTML文件变大

**适用场景**：小图标、动态生成的图表

### Q5: 如何调试JavaScript代码？

**A:**
1. **浏览器开发者工具**（F12）
   - Console面板：查看日志和错误
   - Network面板：查看HTTP请求
   - Elements面板：查看DOM结构

2. **console.log()**
   ```javascript
   console.log('数据:', data);
   console.error('错误:', error);
   ```

3. **断点调试**
   ```javascript
   debugger;  // 代码执行到这里会暂停
   ```

---

## 📝 汇报提纲

### 1. ORM表结构设计（5分钟）
- ✅ predictions表的18个字段设计思路
- ✅ 数据类型选择依据（Integer/Float/String/Text/JSON）
- ✅ 主键、外键、索引的设计
- ✅ 预留users表但未启用（说明原因）

### 2. 预测记录自动持久化（5分钟）
- ✅ 单次预测保存流程（代码演示）
- ✅ 批量预测保存流程（事务保证一致性）
- ✅ 批次ID的设计（UUID生成）
- ✅ 统计数据查询（各风险等级计数）

### 3. 前端AJAX异步交互流程（5分钟）
- ✅ Fetch API vs 传统AJAX
- ✅ async/await简化异步代码
- ✅ FormData处理表单数据
- ✅ 错误处理机制（try-catch）

### 4. 6种统计图表的动态生成与切换（5分钟）
- ✅ 前端按钮绑定事件（data-*属性）
- ✅ Base64图片传输原理
- ✅ 动态DOM更新（innerHTML）
- ✅ 图表类型与业务含义

### 5. 聚类结果的可视化展示（5分钟）
- ✅ 聚类算法流程（标准化→K-Means→可视化）
- ✅ 簇特征中心的业务解读
- ✅ 3D散点图展示
- ✅ 用户可调整聚类数量

### 6. CSV导出功能（3分钟）
- ✅ Blob API处理文件下载
- ✅ URL.createObjectURL()创建临时链接
- ✅ 前端触发下载的 trick
- ✅ UTF-8编码支持中文

### 7. 现场演示（7分钟）
1. 初始化数据库（`python init_db.py`）
2. 启动Flask应用（`python app.py`）
3. 单条预测 → 查看数据库记录
4. 批量预测 → 查看统计卡片和表格
5. 生成6种图表 → 展示动态切换
6. 执行聚类分析 → 解读结果
7. 导出CSV → 打开文件验证

---

## 🎯 核心竞争优势

1. **完整的MVC架构**：前端、后端、数据库分层清晰
2. **数据持久化**：所有预测记录自动保存，可追溯
3. **丰富的可视化**：6种图表 + 聚类分析，多维度洞察
4. **用户体验优秀**：异步交互、加载动画、实时反馈
5. **代码质量高**：模块化、可扩展、易维护

---

**文档版本**：v1.0  
**最后更新**：2026年5月29日  
**联系方式**：[你的邮箱/电话]
