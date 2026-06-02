---
name: weather
track: bonus
kind: live_api
provider: OpenWeatherMap
requires_env: [OPENWEATHER_API_KEY]
inputs: [city]
outputs: [temperature, condition]
side_effect: false
---
# weather
Lấy thông tin nhiệt độ và tình trạng thời tiết hiện tại cho một thành phố cụ thể.