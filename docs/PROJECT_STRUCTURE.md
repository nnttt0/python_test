# 项目模块说明

## 目录结构

```
experiment/
├── person1_data_model/          # 人一：数据预处理与模型训练
│   ├── DataProcess.py           # 数据清洗、编码
│   └── train.py                 # 模型训练
│
├── person2_backend/             # 人二：后端架构与API路由
│   ├── app.py                   # Flask主应用
│   └── config.py                # 全局配置
│
├── person3_ml_services/         # 人三：机器学习模型与业务服务
│   ├── models/                  # 机器学习模型
│   │   ├── predictor.py         # 预测器
│   │   └── cluster.py           # 聚类分析
│   └── services/                # 业务服务
│       ├── data_processor.py    # 数据处理
│       └── visualizer.py        # 可视化
│
├── person4_database_frontend/   # 人四：数据库持久化与前端交互
│   ├── database/                # 数据库层
│   │   ├── db.py                # 连接管理
│   │   ├── models.py            # ORM模型
│   │   ├── services.py          # CRUD服务
│   │   └── config.py            # 数据库配置
│   ├── templates/               # HTML模板
│   │   └── index.html
│   ├── static/                  # 静态资源
│   │   ├── css/style.css
│   │   └── js/main.js
│   └── init_db.py               # 数据库初始化
│
├── DataSet/                     # 数据集（公共）
├── model/                       # 训练好的模型（公共）
├── uploads/                     # 上传文件（公共）
├── docs/                        # 文档（公共）
├── requirements.txt             # 依赖（公共）
└── README.md                    # 项目说明（公共）
```

## 运行方式

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 初始化数据库（人四）
```bash
cd person4_database_frontend
python init_db.py
```

### 3. 训练模型（人一）
```bash
cd person1_data_model
python DataProcess.py
python train.py
```

### 4. 启动应用（人二）
```bash
cd person2_backend
python app.py
```

访问: http://localhost:8888
