import os
import sys
import asyncio
import threading
import queue
import logging
import requests

# 確保本檔所在目錄在 import 路徑上 (環境可能啟用 PYTHONSAFEPATH)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
from google import genai

import providers

# Load Env with override
load_dotenv(override=True)
# 有效金鑰解析：優先環境變數 GEMINI_API_KEY，其次 .env 的 GOOGLE_API_KEY
API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if API_KEY:
    print(f"🔑 API Key loaded (starts with): {API_KEY[:6]}...")
else:
    print("❌ API Key NOT found! (set GEMINI_API_KEY or GOOGLE_API_KEY)")

# App Setup
app = Flask(__name__)
app.config['SECRET_KEY'] = 'gemini_secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gemini Live realtime 模型 (即時語音對話模式)
# gemini-3.5-live-translate-preview：3.5、專為即時翻譯設計，原生語音 AUDIO 輸出
# （若即時翻譯品質或行為異常，可回退 gemini-3.1-flash-live-preview）
LIVE_MODEL = "gemini-3.5-live-translate-preview"

# Session Storage: Key: sid, Value: GeminiSession
active_sessions = {}
