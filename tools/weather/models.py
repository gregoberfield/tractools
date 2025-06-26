from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()

class WeatherData(db.Model):
    __tablename__ = 'weather_data'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10), nullable=False)
    time = db.Column(db.String(15), nullable=False)
    temperature_f = db.Column(db.Float, nullable=False)
    humidity_percent = db.Column(db.Float, nullable=False)
    dew_point_f = db.Column(db.Float, nullable=False)
    barometer_mb = db.Column(db.Float, nullable=False)
    wind_speed_mph = db.Column(db.Float, nullable=False)
    wind_direction_degrees = db.Column(db.Float, nullable=False)
    rain_rate_mm_per_hour = db.Column(db.Float, nullable=False)
    sky_temperature_f = db.Column(db.Float, nullable=False)
    sky_condition = db.Column(db.String(50), nullable=False)
    wind_condition = db.Column(db.String(50), nullable=False)
    rain_condition = db.Column(db.String(50), nullable=False)
    daylight_condition = db.Column(db.String(50), nullable=False)
    roof_close_requested = db.Column(db.Boolean, nullable=False, default=False)
    alert_condition = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date,
            'time': self.time,
            'temperature_f': self.temperature_f,
            'humidity_percent': self.humidity_percent,
            'dew_point_f': self.dew_point_f,
            'barometer_mb': self.barometer_mb,
            'wind_speed_mph': self.wind_speed_mph,
            'wind_direction_degrees': self.wind_direction_degrees,
            'rain_rate_mm_per_hour': self.rain_rate_mm_per_hour,
            'sky_temperature_f': self.sky_temperature_f,
            'sky_condition': self.sky_condition,
            'wind_condition': self.wind_condition,
            'rain_condition': self.rain_condition,
            'daylight_condition': self.daylight_condition,
            'roof_close_requested': self.roof_close_requested,
            'alert_condition': self.alert_condition,
            'created_at': self.created_at.replace(tzinfo=timezone.utc).isoformat() if self.created_at else None
        }