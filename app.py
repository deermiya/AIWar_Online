"""
AI 狼人杀 - Flask 后端
用法：
  1. pip install flask requests google-genai python-dotenv
  2. 在下方填入你的 API Key
  3. python app.py
  4. 浏览器打开 http://localhost:15000
"""

from flask import Flask, request, jsonify, send_file, Response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests
import time
import os
import asyncio
import edge_tts
from google import genai
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix

# 加载 .env 配置文件
load_dotenv()

app = Flask(__name__)
# 信任代理服务器传递的 X-Forwarded-* 请求头（防刷限流需要真实 IP）
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)


# ╔══════════════════════════════════════════════╗
# ║  配置防刷限流器 (保护线上 API Key)             ║
# ╚══════════════════════════════════════════════╝
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["1000 per day", "100 per hour"],
    storage_uri="memory://",
)

# ╔══════════════════════════════════════════════╗
# ║        在这里填入你的 API Key                ║
# ╚══════════════════════════════════════════════╝

DOUBAO_KEY     = os.environ.get("DOUBAO_KEY")
DEEPSEEK_KEY   = os.environ.get("DEEPSEEK_KEY")
GEMINI_KEY     = os.environ.get("GEMINI_KEY")
OPENROUTER_KEY = os.environ.get("OPENROUTER_KEY")
MIMO_KEY       = os.environ.get("MIMO_KEY")




# ╔══════════════════════════════════════════════╗
# ║        各 API 渠道配置 (Endpoints)             ║
# ╚══════════════════════════════════════════════╝
# 你可以在这里统一定义可用的 API 模型。

ENDPOINTS = {
    "doubao": {
        "url":   "https://token-plan-cn.xiaomimimo.com/v1/chat/completions",
        "key":   MIMO_KEY,
        "model": "doubao-pro-32k",
    },
    "deepseek": {
        "url":   "https://token-plan-cn.xiaomimimo.com/v1/chat/completions",
        "key":   MIMO_KEY,
        "model": "deepseek-chat",
    },
    "gemini": {
        "url":   "https://token-plan-cn.xiaomimimo.com/v1/chat/completions",
        "key":   MIMO_KEY,
        "model": "gemini-1.5-pro",
    },
    "gpt": {
        "url":   "https://token-plan-cn.xiaomimimo.com/v1/chat/completions",
        "key":   MIMO_KEY,
        "model": "gpt-4o",
    },
    "claude": {
        "url":   "https://token-plan-cn.xiaomimimo.com/v1/chat/completions",
        "key":   MIMO_KEY,
        "model": "claude-3-5-sonnet-20240620",
    },
    "grok": {
        "url":   "https://token-plan-cn.xiaomimimo.com/v1/chat/completions",
        "key":   MIMO_KEY,
        "model": "grok-beta",
    },
    "qwen": {
        "url":   "https://token-plan-cn.xiaomimimo.com/v1/chat/completions",
        "key":   MIMO_KEY,
        "model": "qwen-max",
    },
    "mimo": {
        "url":   "https://token-plan-cn.xiaomimimo.com/v1/chat/completions",
        "key":   MIMO_KEY,
        "model": "mimo-v2.5-pro",
    },
}

# ╔══════════════════════════════════════════════╗
# ║        玩家绑定哪个 API 模型                   ║
# ╚══════════════════════════════════════════════╝
# 这里决定了前端 6 个玩家各自调用上面哪个 endpoint。
# 如果你想让 6 个人都用 DeepSeek，就把后面的值全改成 "deepseek"

PLAYER_ENDPOINTS = {
    "Doubao":   "doubao",
    "DeepSeek": "deepseek",
    "Gemini":   "gemini",
    "ChatGPT":  "gpt",
    "Claude":   "claude",
    "Grok":     "grok",
    "Qwen":     "qwen",
    "MiMo":     "mimo",
}



# ╔══════════════════════════════════════════════╗
# ║  Edge-TTS 云端免费音色配置                   ║
# ╚══════════════════════════════════════════════╝
# 使用免费的 Edge TTS 替代本地的 CosyVoice，以便在线上环境部署

VOICE_MAP = {
    "Doubao": "zh-CN-XiaoyiNeural",       # 甜美
    "DeepSeek": "zh-CN-YunxiNeural",      # 男声
    "ChatGPT": "zh-CN-XiaoxiaoNeural",    # 经典女声
    "Claude": "zh-CN-ZhenzheNeural",      # 稳重男声
    "Gemini": "zh-CN-YunjianNeural",      # 男声
    "Grok": "zh-CN-XiaozhenNeural",       # 女声
    "Qwen": "zh-CN-YunxiaNeural",         # 少年音
    "MiMo": "zh-CN-XiaoyiNeural",         # 甜美女声
}


@app.route("/")
def index():
    return send_file("index.html")


@app.route("/static/icons/<path:filename>")
def serve_icon(filename):
    return send_file(os.path.join("static", "icons", filename))


@app.route("/api/chat", methods=["POST"])
@limiter.limit("20 per minute")  # 限制频率
def chat():
    """通用聊天接口，前端传 player 名字 + prompt，后端路由到对应 API"""
    data = request.json
    player = data.get("player", "")
    system_msg = data.get("system", "")
    user_msg = data.get("message", "")

    if player not in PLAYER_ENDPOINTS:
        return jsonify({"error": f"未知玩家: {player}"}), 400

    endpoint_name = PLAYER_ENDPOINTS[player]
    if endpoint_name not in ENDPOINTS:
        return jsonify({"error": f"玩家绑定的接口未配置: {endpoint_name}"}), 500

    cfg = ENDPOINTS[endpoint_name]


    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {cfg['key']}",
    }

    payload = {
        "model": cfg["model"],
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        "max_tokens": 500,
        "temperature": 0.9,
    }

    try:
        resp = requests.post(cfg["url"], headers=headers, json=payload, timeout=60)
        if resp.status_code == 429:
            time.sleep(4)
            resp = requests.post(cfg["url"], headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        result = resp.json()
        if "choices" not in result:
            err = result.get("error", {})
            msg = err.get("message", str(result)) if isinstance(err, dict) else str(err)
            return jsonify({"error": f"{player}: {msg}"}), 500
        content = result["choices"][0]["message"]["content"]
        return jsonify({"content": content, "player": player, "model": cfg["model"]})
    except requests.exceptions.Timeout:
        return jsonify({"error": f"{player} 响应超时"}), 504
    except Exception as e:
        return jsonify({"error": f"{player}: {str(e)}"}), 500


TTS_CACHE = {}

async def generate_edge_tts(text, voice):
    communicate = edge_tts.Communicate(text, voice)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

@app.route("/api/tts", methods=["POST"])
@limiter.limit("30 per minute")
def tts():
    """文字转语音接口，使用 edge-tts"""
    data = request.json
    player = data.get("player", "")
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "文本为空"}), 400

    cache_key = (player, text)
    if cache_key in TTS_CACHE: 
        return Response(TTS_CACHE[cache_key], mimetype="audio/mpeg")

    voice = VOICE_MAP.get(player, "zh-CN-XiaoxiaoNeural")

    try:
        audio = asyncio.run(generate_edge_tts(text, voice))
        TTS_CACHE[cache_key] = audio
        return Response(audio, mimetype="audio/mpeg")
    except Exception as e:
        return jsonify({"error": f"TTS生成失败: {str(e)}"}), 500

@app.route("/api/health")
def health():
    """检查各 API 配置状态"""
    status = {}
    for name, endpoint in PLAYER_ENDPOINTS.items():
        if endpoint in ENDPOINTS:
            cfg = ENDPOINTS[endpoint]
            has_key = cfg["key"] not in ("", "在这里填入你的Key", None)
            status[name] = {
                "endpoint": endpoint,
                "model": cfg["model"],
                "key_configured": has_key,
                "url": cfg["url"],
            }
        else:
            status[name] = {"error": f"未知的接口: {endpoint}"}
    return jsonify(status)


if __name__ == "__main__":
    print("\nDEER杯AI狼人杀 服务器启动中...")
    print("打开浏览器访问: http://localhost:15000")
    print("按 Ctrl+C 停止服务器\n")
    app.run(host="0.0.0.0", debug=True, port=15000)
