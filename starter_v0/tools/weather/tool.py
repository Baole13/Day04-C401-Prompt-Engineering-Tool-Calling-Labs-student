from typing import Any

def get_weather(city: str = "Hanoi") -> dict[str, Any]:
    # Đây là logic giả lập. Nếu muốn nâng cao, bạn có thể gọi API thật của OpenWeatherMap
    # Để đơn giản cho Lab, ta trả về dữ liệu mẫu:
    return {
        "tool": "weather",
        "city": city,
        "temperature": "28°C",
        "condition": "Có nắng nhẹ"
    }