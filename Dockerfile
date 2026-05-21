# 使用官方 Python 轻量级基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 复制依赖列表并安装
# 这里加上 --no-cache-dir 可以减小镜像体积
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目所有文件到容器内
COPY . .

# 暴露 Gunicorn 运行的端口
EXPOSE 15000

# 使用 Gunicorn 启动应用，2 个 worker 进程可以根据服务器配置调整
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:15000", "app:app"]
