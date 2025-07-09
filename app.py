from flask import Flask, request, render_template, redirect, url_for
import requests
from twilio.rest import Client

app = Flask(__name__)

WEATHER_API_KEY = '58802e19f52daf91cae2b67b39157d1e'
WEATHER_API_URL = 'http://api.openweathermap.org/data/2.5/forecast'
TWILIO_ACCOUNT_SID = 'AC1357b007fc31e84dbd34fcdd3df47f43'
TWILIO_AUTH_TOKEN = '0d08e894b9cf536ccd96b5aafb16f0a8'
TWILIO_PHONE_NUMBER = '+14782538620'
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def get_weather_forecast(city):
    params = {'q': city, 'appid': WEATHER_API_KEY, 'units': 'metric'}
    response = requests.get(WEATHER_API_URL, params=params)
    return response.json() if response.status_code == 200 else None

def send_alert(phone_number, message):
    client.messages.create(to=phone_number, from_=TWILIO_PHONE_NUMBER, body=message)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        city = request.form['city']
        phone = request.form['phone']
        forecast = get_weather_forecast(city)
        if forecast:
            return redirect(url_for('forecast', city=city, phone=phone))
    return render_template('index.html')

@app.route('/forecast')
def forecast():
    city = request.args.get('city')
    phone = request.args.get('phone')
    forecast = get_weather_forecast(city)
    daily_weather = {}
    alert_message = ''

    if forecast and 'list' in forecast:
        for entry in forecast['list']:
            date = entry['dt_txt'].split()[0]
            if date not in daily_weather:
                daily_weather[date] = {
                    'temp': [],
                    'humidity': [],
                    'pressure': [],
                    'weather_description': entry['weather'][0]['main'],
                    'hourly': []
                }

            # Aggregate daily information
            daily_weather[date]['temp'].append(entry['main']['temp'])
            daily_weather[date]['humidity'].append(entry['main']['humidity'])
            daily_weather[date]['pressure'].append(entry['main']['pressure'])
            daily_weather[date]['hourly'].append({
                'time': entry['dt_txt'].split()[1],
                'temp': entry['main']['temp'],
                'weather_description': entry['weather'][0]['description'],
                'humidity': entry['main']['humidity'],
                'pressure': entry['main']['pressure'],
                'wind_speed': entry['wind']['speed']
            })

        weather_details = []
        for date, data in list(daily_weather.items())[:7]:  # Limit to 7 days
            avg_temp = sum(data['temp']) / len(data['temp'])
            max_temp = max(data['temp'])
            min_temp = min(data['temp'])
            alert_needed = max_temp > 48 or min_temp < 15
            if alert_needed:
                alert_message = f"Extreme temperature on {date}. Please change the precautinory measures and use umberella in rainy days"

            weather_details.append({
                'date': date,
                'avg_temp': avg_temp,
                'min_temp': min_temp,
                'max_temp': max_temp,
                'weather_description': data['weather_description'],
                'humidity': sum(data['humidity']) / len(data['humidity']),
                'pressure': sum(data['pressure']) / len(data['pressure']),
                'hourly': data['hourly'],
                'alert_needed': alert_needed
            })

        if alert_message:
            send_alert(phone, alert_message)

    return render_template('forecast.html', city=city, weather_details=weather_details, alert_message=alert_message)

@app.route('/hourly/<date>')
def hourly(date):
    city = request.args.get('city')
    forecast = get_weather_forecast(city)
    daily_forecast = []

    if forecast and 'list' in forecast:
        for entry in forecast['list']:
            if entry['dt_txt'].startswith(date):
                daily_forecast.append({
                    'time': entry['dt_txt'].split()[1],
                    'temp': entry['main']['temp'],
                    'weather_description': entry['weather'][0]['description'],
                    'humidity': entry['main']['humidity'],
                    'pressure': entry['main']['pressure'],
                    'wind_speed': entry['wind']['speed']
                })

    return render_template('hourly.html', date=date, city=city, daily_forecast=daily_forecast)

if __name__ == '__main__':
    app.run(debug=True)

