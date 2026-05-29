# MySQL 数据库配置指南

## 1. 安装依赖

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 2. 配置 MySQL 数据库

### 方式一：修改配置文件

编辑 `database/config.py` 文件：

```python
MYSQL_HOST = 'localhost'        # 数据库主机
MYSQL_PORT = '3306'             # 数据库端口
MYSQL_USER = 'root'             # 用户名
MYSQL_PASSWORD = 'your_password' # 密码
MYSQL_DATABASE = 'stroke_prediction' # 数据库名
```

### 方式二：使用环境变量

复制 `.env.example` 为 `.env`，然后修改配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，设置您的 MySQL 连接信息。

## 3. 初始化数据库

运行初始化脚本：

```bash
python init_db.py
```

该脚本会：
- 测试 MySQL 连接
- 创建数据库（如果不存在）
- 创建数据表

## 4. 启动应用

```bash
python app.py
```

## 5. 数据库表结构

### predictions 表（预测记录）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| gender | VARCHAR(20) | 性别 |
| age | FLOAT | 年龄 |
| hypertension | INT | 高血压（0/1） |
| heart_disease | INT | 心脏病（0/1） |
| ever_married | VARCHAR(10) | 婚姻状况 |
| work_type | VARCHAR(50) | 工作类型 |
| residence_type | VARCHAR(20) | 居住类型 |
| avg_glucose_level | FLOAT | 平均血糖水平 |
| bmi | FLOAT | BMI指数 |
| smoking_status | VARCHAR(50) | 吸烟状况 |
| risk_score | FLOAT | 风险分数（0-1） |
| risk_percent | FLOAT | 风险百分比（0-100） |
| risk_level | VARCHAR(20) | 风险等级（safe/warning/danger） |
| suggestion | TEXT | 建议 |
| prediction_type | VARCHAR(20) | 预测类型（single/batch） |
| batch_id | VARCHAR(50) | 批次ID |
| created_at | DATETIME | 创建时间 |
| extra_info | JSON | 额外信息 |

## 6. 数据库操作示例

### 查询所有预测记录

```python
from database import get_db, PredictionService

db = next(get_db())
predictions = PredictionService.get_all_predictions(db, limit=10)
for p in predictions:
    print(p.to_dict())
```

### 查询统计数据

```python
from database import get_db, PredictionService

db = next(get_db())
stats = PredictionService.get_statistics(db)
print(f"总记录数: {stats['total']}")
print(f"高风险: {stats['high_risk']}")
print(f"中风险: {stats['medium_risk']}")
print(f"低风险: {stats['low_risk']}")
```

## 7. 常见问题

### Q: 连接失败怎么办？

A: 请检查：
1. MySQL 服务是否已启动
2. 用户名和密码是否正确
3. 数据库是否已创建
4. 防火墙是否阻止了连接

### Q: 如何查看数据库中的数据？

A: 可以使用以下工具：
- MySQL Workbench
- Navicat
- DBeaver
- 命令行：`mysql -u root -p stroke_prediction`

### Q: 如何备份数据库？

A: 使用 mysqldump：

```bash
mysqldump -u root -p stroke_prediction > backup.sql
```

### Q: 如何恢复数据库？

A: 使用以下命令：

```bash
mysql -u root -p stroke_prediction < backup.sql
```
