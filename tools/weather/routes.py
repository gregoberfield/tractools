from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required
from .models import WeatherData, db
from .astronomy import AstronomyCalculator
from .chart_generator import WeatherChartGenerator
import logging
import time
from functools import lru_cache

logger = logging.getLogger(__name__)
weather_bp = Blueprint('weather', __name__)

# Simple cache for weather data (TTL: 60 seconds)
_weather_cache = {}
_cache_ttl = 60

def _get_cached_weather_data():
    """Get cached weather data or fetch from database"""
    current_time = time.time()
    cache_key = 'latest_weather'
    
    # Check if cache is valid
    if (cache_key in _weather_cache and 
        current_time - _weather_cache[cache_key]['timestamp'] < _cache_ttl):
        return _weather_cache[cache_key]['data']
    
    # Fetch fresh data
    latest_weather = WeatherData.query.order_by(WeatherData.created_at.desc()).first()
    
    # Cache the result
    _weather_cache[cache_key] = {
        'data': latest_weather,
        'timestamp': current_time
    }
    
    return latest_weather

@weather_bp.route('/status')
def get_status():
    """Get weather status page"""
    try:
        latest_weather = _get_cached_weather_data()
        
        # Get historical data for last 24 hours based on actual observation time
        from datetime import datetime, timedelta
        # Use local time since date/time fields store CDT timestamps
        twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
        current_date = twenty_four_hours_ago.strftime('%Y-%m-%d')
        current_time = twenty_four_hours_ago.strftime('%H:%M:%S')
        
        # Query using date/time fields for accurate 24-hour rolling window
        historical_data = WeatherData.query.filter(
            (WeatherData.date > current_date) | 
            ((WeatherData.date == current_date) & (WeatherData.time >= current_time))
        ).order_by(WeatherData.date.desc(), WeatherData.time.desc()).all()
        
        # Calculate astronomical zones for the time period (with reduced logging)
        astro_calc = AstronomyCalculator()
        astronomical_zones = []
        if historical_data:
            # Use the actual observation times from date/time fields
            import pandas as pd
            observation_times = []
            for data in historical_data:
                obs_time = pd.to_datetime(f"{data.date} {data.time}", format='mixed')
                observation_times.append(obs_time)
            
            start_time = min(observation_times)
            end_time = max(observation_times)
            astronomical_zones = astro_calc.calculate_zones_for_timerange(
                start_time, end_time, interval_minutes=15  # Reduced frequency for performance
            )
            logger.debug(f"Generated {len(astronomical_zones)} astronomical zones")
        
        # Generate charts server-side
        chart_generator = WeatherChartGenerator()
        historical_data_dicts = [data.to_dict() for data in historical_data]
        
        temperature_chart = chart_generator.generate_temperature_chart(historical_data_dicts, astronomical_zones)
        humidity_chart = chart_generator.generate_humidity_chart(historical_data_dicts, astronomical_zones)
        wind_speed_chart = chart_generator.generate_wind_speed_chart(historical_data_dicts, astronomical_zones)
        
        if request.headers.get('Accept') == 'application/json':
            return jsonify({
                'current_weather': latest_weather.to_dict() if latest_weather else {},
                'historical_data': historical_data_dicts,
                'astronomical_zones': astronomical_zones
            })
        else:
            return render_template('tools/weather/status.html', 
                                 current_weather=latest_weather if latest_weather else None,
                                 historical_data=historical_data_dicts,
                                 astronomical_zones=astronomical_zones,
                                 temperature_chart=temperature_chart,
                                 humidity_chart=humidity_chart,
                                 wind_speed_chart=wind_speed_chart)
    except Exception as e:
        logger.error(f"Error getting weather status: {e}")
        if request.headers.get('Accept') == 'application/json':
            return jsonify({'error': str(e)}), 500
        else:
            return render_template('tools/weather/status.html', 
                                 error=str(e), 
                                 current_weather=None,
                                 historical_data=[],
                                 astronomical_zones=[],
                                 temperature_chart="",
                                 humidity_chart="",
                                 wind_speed_chart="")

@weather_bp.route('/api/weatherdata', methods=['POST'])
def update_weather_data():
    """API endpoint to receive weather data updates"""
    try:
        if not request.is_json:
            return jsonify({
                'status': 'error',
                'message': 'Content-Type must be application/json'
            }), 400
        
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No JSON data provided'
            }), 400
        
        required_fields = [
            'date', 'time', 'temperature_f', 'humidity_percent', 'dew_point_f',
            'wind_speed_mph', 'rain_rate_mm_per_hour', 'sky_temperature_f', 
            'sky_condition', 'wind_condition', 'rain_condition', 
            'daylight_condition', 'roof_close_requested', 'alert_condition'
        ]
        
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Check if data already exists for this date/time combination
        existing_data = WeatherData.query.filter_by(
            date=data['date'],
            time=data['time']
        ).first()
        
        if existing_data:
            return jsonify({
                'status': 'success',
                'message': 'Weather data already exists for this date/time',
                'id': existing_data.id
            }), 200
        
        weather_data = WeatherData(
            date=data['date'],
            time=data['time'],
            temperature_f=data['temperature_f'],
            humidity_percent=data['humidity_percent'],
            dew_point_f=data['dew_point_f'],
            barometer_mb=data.get('barometer_mb', 0.0),
            wind_speed_mph=data['wind_speed_mph'],
            wind_direction_degrees=data.get('wind_direction_degrees', 0.0),
            rain_rate_mm_per_hour=data['rain_rate_mm_per_hour'],
            sky_temperature_f=data['sky_temperature_f'],
            sky_condition=data['sky_condition'],
            wind_condition=data['wind_condition'],
            rain_condition=data['rain_condition'],
            daylight_condition=data['daylight_condition'],
            roof_close_requested=data['roof_close_requested'],
            alert_condition=data['alert_condition']
        )
        
        db.session.add(weather_data)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Weather data updated successfully',
            'id': weather_data.id
        }), 201
        
    except Exception as e:
        logger.error(f"Error processing weather data update: {e}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500

@weather_bp.route('/api/latest')
def api_get_latest_weather():
    """API endpoint to get latest weather data"""
    try:
        latest_weather = WeatherData.query.order_by(WeatherData.created_at.desc()).first()
        
        if not latest_weather:
            return jsonify({'error': 'No weather data found'}), 404
            
        return jsonify(latest_weather.to_dict())
    except Exception as e:
        logger.error(f"Error getting latest weather data: {e}")
        return jsonify({'error': str(e)}), 500

@weather_bp.route('/api/history')
def api_get_weather_history():
    """API endpoint to get weather data history"""
    try:
        limit = request.args.get('limit', 100, type=int)
        weather_history = WeatherData.query.order_by(WeatherData.created_at.desc()).limit(limit).all()
        
        return jsonify([weather.to_dict() for weather in weather_history])
    except Exception as e:
        logger.error(f"Error getting weather history: {e}")
        return jsonify({'error': str(e)}), 500

@weather_bp.route('/admin/cache/stats')
@login_required
def get_cache_stats():
    """Admin endpoint to get chart cache statistics"""
    try:
        chart_generator = WeatherChartGenerator()
        stats = chart_generator.get_cache_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return jsonify({'error': str(e)}), 500

@weather_bp.route('/admin/cache/clear', methods=['POST'])
@login_required
def clear_cache():
    """Admin endpoint to clear chart cache"""
    try:
        chart_generator = WeatherChartGenerator()
        cleared_count = chart_generator.clear_cache()
        logger.info(f"Admin cleared {cleared_count} chart cache entries")
        return jsonify({
            'status': 'success',
            'message': f'Cleared {cleared_count} cache entries'
        })
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return jsonify({'error': str(e)}), 500