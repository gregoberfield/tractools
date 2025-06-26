"""
Chart generation module for weather data using matplotlib and seaborn.
Generates server-side charts with astronomical background shading.
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple
import io
import base64
import logging
import time
import pytz
from .chart_cache import get_chart_cache

logger = logging.getLogger(__name__)

# Set matplotlib and seaborn style
plt.style.use('default')
sns.set_palette("husl")

class WeatherChartGenerator:
    """Generate weather charts with astronomical background shading."""
    

    def __init__(self):
        """Initialize the chart generator."""
        # Configure matplotlib for better-looking charts
        plt.rcParams.update({
            'figure.figsize': (12, 6),
            'figure.dpi': 100,
            'savefig.dpi': 150,
            'savefig.bbox': 'tight',
            'savefig.pad_inches': 0.1,
            'font.size': 10,
            'axes.titlesize': 12,
            'axes.labelsize': 10,
            'xtick.labelsize': 9,
            'ytick.labelsize': 9,
            'legend.fontsize': 9,
            'lines.linewidth': 2,
            'grid.alpha': 0.3
        })
        
        # Since database times are already in CDT, just use a simple label
        self.timezone_name = "CDT"
    
    def _prepare_data(self, historical_data: List[Dict]) -> pd.DataFrame:
        """Convert historical data to pandas DataFrame with proper datetime indexing."""
        if not historical_data:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(historical_data)
        
        # Convert created_at to datetime - database times are already in CDT, use as-is
        # Explicitly avoid timezone inference by pandas
        df['timestamp'] = pd.to_datetime(df['created_at'], utc=False)
        df = df.set_index('timestamp')
        df = df.sort_index()
        
        return df
    
    def _add_astronomical_background(self, ax, astronomical_zones: List[Dict], chart_start: datetime, chart_end: datetime):
        """Add astronomical background shading to the chart."""
        if not astronomical_zones:
            return
        
        # Define colors for different zones
        zone_colors = {
            'day': 'rgba(255, 255, 255, 0.0)',          # Transparent for day
            'civil_twilight': 'rgba(255, 223, 128, 0.3)', # Light yellow
            'nautical_twilight': 'rgba(255, 165, 0, 0.4)', # Orange  
            'astronomical_twilight': 'rgba(128, 0, 128, 0.5)', # Purple
            'night': 'rgba(25, 25, 112, 0.6)'              # Dark blue
        }
        
        # Convert rgba to matplotlib format
        def rgba_to_matplotlib(rgba_str):
            if rgba_str.startswith('rgba('):
                values = rgba_str[5:-1].split(',')
                r, g, b = [int(v.strip()) for v in values[:3]]
                a = float(values[3].strip())
                return (r/255, g/255, b/255, a)
            return (0.5, 0.5, 0.5, 0.1)  # Default gray
        
        # Group consecutive zones of the same type
        current_zone = None
        zone_start_time = None
        
        for i, zone_data in enumerate(astronomical_zones + [None]):  # Add None to process last zone
            zone_type = zone_data['zone'] if zone_data else None
            
            if zone_type != current_zone:
                # Draw the previous zone if it exists
                if current_zone and zone_start_time:
                    end_time = zone_data['timestamp'] if zone_data else astronomical_zones[-1]['timestamp']
                    
                    # Treat astronomical zone timestamps the same as database timestamps (already in CDT)
                    # Convert from milliseconds to datetime, but don't do timezone conversion
                    start_dt = datetime.fromtimestamp(zone_start_time / 1000)
                    end_dt = datetime.fromtimestamp(end_time / 1000)
                    
                    # Only draw if within chart range
                    if start_dt < chart_end and end_dt > chart_start:
                        color = rgba_to_matplotlib(zone_colors.get(current_zone, 'rgba(128, 128, 128, 0.1)'))
                        
                        # Add background rectangle
                        ax.axvspan(start_dt, end_dt, alpha=color[3], color=color[:3], zorder=0)
                
                # Start new zone
                current_zone = zone_type
                zone_start_time = zone_data['timestamp'] if zone_data else None
    
    def _calculate_sma(self, data: pd.Series, window: int) -> pd.Series:
        """Calculate Simple Moving Average."""
        return data.rolling(window=window, min_periods=1).mean()
    
    def generate_temperature_chart(self, historical_data: List[Dict], astronomical_zones: List[Dict]) -> str:
        """Generate temperature chart with dew point and sky temperature."""
        # Check cache first
        cache = get_chart_cache()
        cached_image = cache.get('temperature', historical_data, astronomical_zones)
        if cached_image:
            return cached_image
        
        df = self._prepare_data(historical_data)
        if df.empty:
            return self._generate_no_data_chart("No temperature data available")
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Add astronomical background
        self._add_astronomical_background(ax, astronomical_zones, df.index.min(), df.index.max())
        
        # Plot temperature data
        ax.plot(df.index, df['temperature_f'], label='Temperature', color='#ff6384', linewidth=2)
        ax.plot(df.index, df['dew_point_f'], label='Dew Point', color='#4bc0c0', linewidth=2)
        ax.plot(df.index, df['sky_temperature_f'], label='Sky Temperature', color='#9966ff', linewidth=2)
        
        # Customize chart
        ax.set_title('24-Hour Temperature Trends', fontsize=14, fontweight='bold')
        ax.set_ylabel('Temperature (°F)', fontsize=12)
        ax.set_xlabel(f'Time ({self.timezone_name})', fontsize=12)
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        image_data = self._fig_to_base64(fig)
        
        # Cache the generated image
        cache.set('temperature', historical_data, astronomical_zones, image_data)
        
        return image_data
    
    def generate_humidity_chart(self, historical_data: List[Dict], astronomical_zones: List[Dict]) -> str:
        """Generate humidity chart."""
        # Check cache first
        cache = get_chart_cache()
        cached_image = cache.get('humidity', historical_data, astronomical_zones)
        if cached_image:
            return cached_image
        
        df = self._prepare_data(historical_data)
        if df.empty:
            return self._generate_no_data_chart("No humidity data available")
        
        fig, ax = plt.subplots(figsize=(14, 6))
        
        # Add astronomical background
        self._add_astronomical_background(ax, astronomical_zones, df.index.min(), df.index.max())
        
        # Plot humidity data with area fill
        ax.plot(df.index, df['humidity_percent'], label='Humidity (%)', color='#36a2eb', linewidth=2)
        ax.fill_between(df.index, df['humidity_percent'], alpha=0.3, color='#36a2eb')
        
        # Customize chart
        ax.set_title('24-Hour Humidity Trend', fontsize=14, fontweight='bold')
        ax.set_ylabel('Humidity (%)', fontsize=12)
        ax.set_xlabel(f'Time ({self.timezone_name})', fontsize=12)
        ax.set_ylim(0, 100)
        ax.grid(True, alpha=0.3)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        image_data = self._fig_to_base64(fig)
        
        # Cache the generated image
        cache.set('humidity', historical_data, astronomical_zones, image_data)
        
        return image_data
    
    def generate_wind_speed_chart(self, historical_data: List[Dict], astronomical_zones: List[Dict]) -> str:
        """Generate wind speed chart with SMA."""
        # Check cache first
        cache = get_chart_cache()
        cached_image = cache.get('wind_speed', historical_data, astronomical_zones)
        if cached_image:
            return cached_image
        
        df = self._prepare_data(historical_data)
        if df.empty:
            return self._generate_no_data_chart("No wind speed data available")
        
        fig, ax = plt.subplots(figsize=(14, 6))
        
        # Add astronomical background
        self._add_astronomical_background(ax, astronomical_zones, df.index.min(), df.index.max())
        
        # Calculate SMA
        sma_30 = self._calculate_sma(df['wind_speed_mph'], 30)
        
        # Plot wind speed data
        ax.plot(df.index, df['wind_speed_mph'], label='Wind Speed (mph)', color='#ff9f40', linewidth=1.5, alpha=0.8)
        ax.fill_between(df.index, df['wind_speed_mph'], alpha=0.3, color='#ff9f40')
        ax.plot(df.index, sma_30, label='SMA 30', color='#ff6384', linewidth=2)
        
        # Customize chart
        ax.set_title('24-Hour Wind Speed Trend', fontsize=14, fontweight='bold')
        ax.set_ylabel('Wind Speed (mph)', fontsize=12)
        ax.set_xlabel(f'Time ({self.timezone_name})', fontsize=12)
        ax.set_ylim(bottom=0)
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        image_data = self._fig_to_base64(fig)
        
        # Cache the generated image
        cache.set('wind_speed', historical_data, astronomical_zones, image_data)
        
        return image_data
    
    def clear_cache(self) -> int:
        """Clear all cached charts."""
        cache = get_chart_cache()
        return cache.clear_all()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        cache = get_chart_cache()
        cache.clear_expired()  # Clean up expired entries
        return cache.get_stats()
    
    def _generate_no_data_chart(self, message: str) -> str:
        """Generate a placeholder chart when no data is available."""
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.text(0.5, 0.5, message, ha='center', va='center', fontsize=16, 
                transform=ax.transAxes, bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.5))
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def _fig_to_base64(self, fig) -> str:
        """Convert matplotlib figure to base64 encoded string."""
        try:
            buffer = io.BytesIO()
            fig.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
            buffer.seek(0)
            
            # Convert to base64
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close(fig)  # Clean up memory
            buffer.close()
            
            return f"data:image/png;base64,{image_base64}"
        except Exception as e:
            logger.error(f"Error converting figure to base64: {e}")
            plt.close(fig)
            return ""