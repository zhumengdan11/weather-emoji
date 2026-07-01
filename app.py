import os
import requests
import hashlib
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__, static_folder='static', static_url_path='/')

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

def generate_mock(city):
    """生成更丰富的模拟天气数据"""
    seed = int(hashlib.md5(city.encode()).hexdigest()[:8], 16)
    temp = 15 + (seed % 20)
    feels_like = temp - 2 + (seed % 5)
    humidity = 40 + (seed % 40)
    wind = 5 + (seed % 25)
    conditions = ["晴", "多云", "阴", "小雨", "小雪", "晴间多云", "雷阵雨"]
    condition = conditions[seed % len(conditions)]
    # 新增字段
    pressure = 1000 + (seed % 30)
    uv_index = 1 + (seed % 10)
    visibility = 8 + (seed % 12)
    sunrise = "06:30" if seed % 2 == 0 else "07:10"
    sunset = "18:45" if seed % 2 == 0 else "19:20"
    icon = "//cdn.weatherapi.com/weather/64x64/day/116.png"
    return {
        "location": {"name": city},
        "current": {
            "temp_c": temp,
            "condition": {"text": condition, "icon": icon},
            "feelslike_c": feels_like,
            "humidity": humidity,
            "wind_kph": wind,
            "pressure_mb": pressure,
            "uv": uv_index,
            "vis_km": visibility,
            "sunrise": sunrise,
            "sunset": sunset
        }
    }

@app.route('/api/weather')
def weather_proxy():
    city = request.args.get('city', 'Qingdao')
    api_key = os.getenv('SCHOOL_API_KEY')
    base_url = os.getenv('API_BASE_URL', 'http://api.weatherapi.com/v1')

    if api_key and base_url:
        try:
            url = f"{base_url}/current.json"
            params = {'key': api_key, 'q': city, 'aqi': 'no'}
            resp = requests.get(url, params=params, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            print(f"✅ 真实数据: {city} {data['current']['temp_c']}°C")
            return jsonify(data)
        except Exception as e:
            print(f"⚠️ API失败，使用模拟数据: {e}")
    
    mock = generate_mock(city)
    print(f"🎭 模拟数据: {city} {mock['current']['temp_c']}°C")
    return jsonify(mock)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)