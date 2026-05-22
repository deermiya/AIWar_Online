---
title: AIWar Online
emoji: 🎮
colorFrom: blue
colorTo: red
sdk: docker
app_port: 15000
---

# AIWar Online

AI 狼人杀 Flask 应用，使用 Hugging Face Docker Space 部署。

## 运行配置

Space 通过 Gunicorn 在 `15000` 端口提供 Flask 服务。修改端口时，需要让
README 顶部的 `app_port` 与 `Dockerfile` 中暴露的端口保持一致。

当前后端在 `app.py` 中将所有模型玩家都路由到 `MIMO_KEY` 环境变量。部署时把
它设置为 Hugging Face Space Secret，不要上传 `.env`，也不要把密钥写进仓库。

## 部署到 Hugging Face

1. 安装 Hugging Face CLI 并登录：

   ```powershell
   hf auth login
   hf auth whoami
   ```

2. 创建 Fine-grained Access Token，并为 Space 所在的个人命名空间勾选仓库
   读取和写入权限。本项目的目标 Space 是 `deermiya/AIWar_Online`。

3. 首次部署时创建 Docker Space：

   ```powershell
   hf repos create deermiya/AIWar_Online --type space --space-sdk docker --exist-ok
   ```

4. 打开 Space 设置页中的 `Variables and secrets`，添加 Secret：

   ```text
   Name: MIMO_KEY
   Value: <你的 MIMO key>
   ```

5. 只上传 Space 运行所需文件：

   ```powershell
   hf upload deermiya/AIWar_Online . . --type space `
     --include=README.md `
     --include=Dockerfile `
     --include=requirements.txt `
     --include=app.py `
     --include=index.html `
     --include=static/** `
     --exclude=.env `
     --exclude=__pycache__/** `
     --exclude=.git/** `
     --commit-message "Deploy AIWar Online Docker Space"
   ```

6. 查看构建状态：

   ```powershell
   hf spaces info deermiya/AIWar_Online --expand runtime
   ```

   等待运行状态变为 `RUNNING`。

7. 验证运行配置：

   ```powershell
   Invoke-WebRequest -UseBasicParsing `
     https://deermiya-aiwar-online.hf.space/api/health
   ```

   Secret 配置完成并且 Space 重启后，每个模型玩家都应该返回
   `"key_configured": true`。
