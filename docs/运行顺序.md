# 代码运行顺序

## 1. 安装依赖
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 2. 配置数据库
编辑 `database/config.py`，修改：
```python
MYSQL_PASSWORD = 'your_password'  # 改为您的MySQL密码
```

## 3. 初始化数据库
```bash
python init_db.py
```

## 4. 启动应用
```bash
python app.py
```

## 访问应用
浏览器打开：http://localhost:8888
