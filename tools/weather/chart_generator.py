"""
Chart generation module for weather data using matplotlib and seaborn.
Generates server-side charts with astronomical background shading.
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any
import io
import base64
import logging
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
            'figure.figsize': (14, 8),
            'figure.dpi': 100,
            'savefig.dpi': 150,
            'savefig.bbox': 'tight',
            'savefig.pad_inches': 0.1,
            'font.size': 10,
            'axes.titlesize': 14,
            'axes.labelsize': 12,
            'xtick.labelsize': 10,
            'ytick.labelsize': 10,
            'legend.fontsize': 10,
            'lines.linewidth': 2,
            'grid.alpha': 0.3
        })
    
    def _prepare_data(self, historical_data: List[Dict]) -> pd.DataFrame:
        """Convert historical data to pandas DataFrame."""
        if not historical_data:
            return pd.DataFrame()
        
        # Convert to DataFrame (pre-allocate for performance)
        df = pd.DataFrame(historical_data)
        
        # Combine date and time fields efficiently (handle microseconds)
        df['timestamp'] = pd.to_datetime(df['date'] + ' ' + df['time'], format='mixed')
        df = df.set_index('timestamp')
        df = df.sort_index()
        
        # Only log on first chart generation to reduce overhead
        logger.debug(f"Prepared {len(df)} data points")
        
        return df
    
    def _add_astronomical_background(self, ax, astronomical_zones: List[Dict]):
        """Add astronomical background shading to the chart."""
        if not astronomical_zones:
            return
        
        # Pre-define colors for performance (avoid dict lookup in loop)
        zone_colors = {
            'day': (1.0, 1.0, 1.0, 0.0),
            'civil_twilight': (1.0, 0.87, 0.5, 0.3),
            'nautical_twilight': (1.0, 0.65, 0.0, 0.4), 
            'astronomical_twilight': (0.5, 0.0, 0.5, 0.5),
            'night': (0.1, 0.1, 0.44, 0.6)
        }
        
        # Process zones efficiently with reduced object creation
        current_zone = None
        zone_start_time = None
        cdt_offset = timedelta(hours=5)  # Pre-calculate offset
        
        for zone_data in astronomical_zones + [None]:
            zone_type = zone_data['zone'] if zone_data else None
            
            if zone_type != current_zone and current_zone and zone_start_time:
                # Draw the previous zone
                end_time = zone_data['timestamp'] if zone_data else astronomical_zones[-1]['timestamp']
                
                # Efficient datetime conversion
                start_dt = datetime.fromtimestamp(zone_start_time / 1000) - cdt_offset
                end_dt = datetime.fromtimestamp(end_time / 1000) - cdt_offset
                
                # Only draw non-transparent zones
                color = zone_colors.get(current_zone, (0.5, 0.5, 0.5, 0.1))
                if color[3] > 0:  # Skip transparent zones
                    ax.axvspan(start_dt, end_dt, alpha=color[3], color=color[:3], zorder=0)
            
            # Update state
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
        
        # Create figure and axis
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Add astronomical background
        self._add_astronomical_background(ax, astronomical_zones)
        
        # Plot temperature data
        sns.lineplot(data=df, x=df.index, y='temperature_f', label='Temperature', 
                    color='#ff6384', linewidth=2, ax=ax)
        sns.lineplot(data=df, x=df.index, y='dew_point_f', label='Dew Point', 
                    color='#4bc0c0', linewidth=2, ax=ax)
        sns.lineplot(data=df, x=df.index, y='sky_temperature_f', label='Sky Temperature', 
                    color='#9966ff', linewidth=2, ax=ax)
        
        # Customize chart
        ax.set_title('24-Hour Temperature Trends', fontweight='bold')
        ax.set_ylabel('Temperature (°F)')
        ax.set_xlabel('Time (US/Chicago)')
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        
        # Format x-axis for time display
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
        
        # Create figure and axis
        fig, ax = plt.subplots(figsize=(14, 6))
        
        # Add astronomical background
        self._add_astronomical_background(ax, astronomical_zones)
        
        # Plot humidity data with area fill
        sns.lineplot(data=df, x=df.index, y='humidity_percent', label='Humidity (%)', 
                    color='#36a2eb', linewidth=2, ax=ax)
        ax.fill_between(df.index, df['humidity_percent'], alpha=0.3, color='#36a2eb')
        
        # Customize chart
        ax.set_title('24-Hour Humidity Trend', fontweight='bold')
        ax.set_ylabel('Humidity (%)')
        ax.set_xlabel('Time (US/Chicago)')
        ax.set_ylim(0, 100)
        ax.grid(True, alpha=0.3)
        
        # Format x-axis for time display
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
        
        # Create figure and axis
        fig, ax = plt.subplots(figsize=(14, 6))
        
        # Add astronomical background
        self._add_astronomical_background(ax, astronomical_zones)
        
        # Calculate SMA for last 30 data points
        sma_30 = self._calculate_sma(df['wind_speed_mph'], 30)
        
        # Plot wind speed data
        sns.lineplot(data=df, x=df.index, y='wind_speed_mph', label='Wind Speed (mph)', 
                    color='#ff9f40', linewidth=1.5, alpha=0.8, ax=ax)
        ax.fill_between(df.index, df['wind_speed_mph'], alpha=0.3, color='#ff9f40')
        sns.lineplot(data=df, x=df.index, y=sma_30, label='SMA 30', 
                    color='#ff6384', linewidth=2, ax=ax)
        
        # Customize chart
        ax.set_title('24-Hour Wind Speed Trend', fontweight='bold')
        ax.set_ylabel('Wind Speed (mph)')
        ax.set_xlabel('Time (US/Chicago)')
        ax.set_ylim(bottom=0)
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        
        # Format x-axis for time display
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