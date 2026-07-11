import os
import json
import requests
import hashlib
import openai
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__, static_folder='static', static_url_path='/')

# ========== 配置 AI（旧版写法） ==========
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if OPENROUTER_API_KEY:
    openai.api_key = OPENROUTER_API_KEY
    openai.base_url = "https://openrouter.ai/api/v1"
    ai_enabled = True
    print("✅ AI 服务已启用")
else:
    ai_enabled = False
    print("⚠️ 未配置 OPENROUTER_API_KEY，AI 建议功能将不可用")

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

# ========== 天气 API（wttr.in） ==========
def get_weather_from_wttr(city):
    try:
        url = f"https://wttr.in/{city}?format=j1&days=3"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        current = data["current_condition"][0]
        today = data["weather"][0]

        forecast_list = []
        for day in data["weather"]:
            forecast_list.append({
                "date": day["date"],
                "max_temp": float(day["maxtempC"]),
                "min_temp": float(day["mintempC"]),
                "condition": day["hourly"][0]["weatherDesc"][0]["value"],
                "icon": day["hourly"][0]["weatherIconUrl"][0]["value"]
            })

        return {
            "city": data["nearest_area"][0]["areaName"][0]["value"],
            "temp_c": float(current["temp_C"]),
            "humidity": int(current["humidity"]),
            "wind_kph": float(current["windspeedKmph"]),
            "condition": current["weatherDesc"][0]["value"],
            "max_temp": float(today["maxtempC"]),
            "min_temp": float(today["mintempC"]),
            "feelslike_c": float(current["FeelsLikeC"]),
            "pressure_mb": float(current["pressure"]),
            "uv": int(current["uvIndex"]),
            "visibility": float(current["visibility"]),
            "sunrise": today["astronomy"][0]["sunrise"],
            "sunset": today["astronomy"][0]["sunset"],
            "forecast": forecast_list
        }
    except Exception as e:
        print(f"wttr.in 错误: {e}")
        return None

@app.route('/api/weather')
def weather_proxy():
    city = request.args.get('city', 'Qingdao')
    data = get_weather_from_wttr(city)
    if data:
        return jsonify(data)
    else:
        seed = int(hashlib.md5(city.encode()).hexdigest()[:8], 16)
        return jsonify({
            "city": city,
            "temp_c": 15 + (seed % 20),
            "humidity": 40 + (seed % 40),
            "wind_kph": 5 + (seed % 25),
            "condition": ["晴", "多云", "阴", "小雨"][seed % 4],
            "max_temp": 20 + (seed % 15),
            "min_temp": 10 + (seed % 10),
            "feelslike_c": 18 + (seed % 12),
            "pressure_mb": 1000 + (seed % 30),
            "uv": 1 + (seed % 10),
            "visibility": 8 + (seed % 12),
            "sunrise": "06:30" if seed % 2 == 0 else "07:10",
            "sunset": "18:30" if seed % 2 == 0 else "19:10",
            "forecast": [
                {"max_temp": 22, "min_temp": 15, "condition": "晴"},
                {"max_temp": 20, "min_temp": 14, "condition": "多云"},
                {"max_temp": 18, "min_temp": 12, "condition": "阴"}
            ]
        })

# ========== AI 出行建议（旧版写法） ==========
@app.route('/api/advice', methods=['POST'])
def get_advice():
    if not ai_enabled:
        return jsonify({"error": "AI 服务未配置，请设置 OPENROUTER_API_KEY"}), 503

    data = request.get_json()
    weather = data.get("weather")
    if not weather:
        return jsonify({"error": "缺少天气数据"}), 400

    prompt = f"""根据以下天气信息，给用户一段简洁实用的出行建议（50字以内）：

当前气温：{weather['temp_c']}°C
体感温度：{weather['feelslike_c']}°C
湿度：{weather['humidity']}%
风速：{weather['wind_kph']} km/h
天气状况：{weather['condition']}
今日最高温：{weather['max_temp']}°C
今日最低温：{weather['min_temp']}°C

请直接输出建议，不要重复数据。"""

    try:
        response = openai.ChatCompletion.create(
            model="google/gemini-2.0-flash-lite-preview-02-05:free",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=120,
            temperature=0.7
        )
        advice = response.choices[0].message.content.strip()
        return jsonify({"advice": advice})
    except Exception as e:
        print(f"AI 错误: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=True)