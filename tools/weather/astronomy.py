"""
Astronomical calculations for weather monitoring system.
Provides twilight calculations and darkness zone classifications.
"""

from datetime import datetime, timezone
import logging
from typing import Dict, List, Tuple
from astropy.time import Time
from astropy.coordinates import EarthLocation, AltAz, get_sun
from astropy import units as u
from config import Config

logger = logging.getLogger(__name__)

class AstronomyCalculator:
    """Calculate astronomical phenomena for weather monitoring."""
    
    def __init__(self):
        """Initialize the astronomy calculator with observatory location."""
        self.latitude = Config.OBSERVATORY_LATITUDE
        self.longitude = Config.OBSERVATORY_LONGITUDE
        self.elevation = Config.OBSERVATORY_ELEVATION
        
        if self.latitude == 0.0 and self.longitude == 0.0:
            logger.warning("Observatory location not configured. Using default coordinates (0,0). Please set OBSERVATORY_LATITUDE and OBSERVATORY_LONGITUDE environment variables.")
        
        logger.info(f"Astronomy calculator initialized for location: {self.latitude} degrees, {self.longitude} degrees, {self.elevation}m")
        
        self.location = EarthLocation(
            lat=self.latitude * u.deg,
            lon=self.longitude * u.deg,
            height=self.elevation * u.m
        )
    
    def get_sun_altitude(self, dt: datetime) -> float:
        """
        Calculate the sun's altitude at a given datetime.
        
        Args:
            dt: Datetime to calculate sun altitude for (assumed to be in local time CDT)
            
        Returns:
            Sun altitude in degrees (negative means below horizon)
        """
        # Convert to UTC for astropy calculations
        if dt.tzinfo is None:
            # Assume input time is already in UTC (timestamps from astronomical zones)
            dt_utc = dt.replace(tzinfo=timezone.utc)
        else:
            dt_utc = dt.astimezone(timezone.utc)
        
        time = Time(dt_utc)
        sun = get_sun(time)
        altaz_frame = AltAz(obstime=time, location=self.location)
        sun_altaz = sun.transform_to(altaz_frame)
        
        return sun_altaz.alt.degree
    
    def classify_darkness_zone(self, sun_altitude: float) -> str:
        """
        Classify the darkness zone based on sun altitude.
        
        Args:
            sun_altitude: Sun altitude in degrees
            
        Returns:
            String classification of darkness zone
        """
        if sun_altitude > 0:  # Above horizon
            return "day"
        elif sun_altitude > -6:   # Civil twilight
            return "civil_twilight"
        elif sun_altitude > -12:  # Nautical twilight
            return "nautical_twilight"
        elif sun_altitude > -18:  # Astronomical twilight
            return "astronomical_twilight"
        else:                     # True darkness
            return "night"
    
    def get_darkness_zone(self, dt: datetime) -> str:
        """
        Get the darkness zone classification for a given datetime.
        
        Args:
            dt: Datetime to classify
            
        Returns:
            String classification of darkness zone
        """
        try:
            sun_altitude = self.get_sun_altitude(dt)
            return self.classify_darkness_zone(sun_altitude)
        except Exception as e:
            logger.error(f"Error calculating darkness zone for {dt}: {e}")
            return "unknown"
    
    def get_zone_color(self, zone: str) -> str:
        """
        Get the background color for a darkness zone.
        
        Args:
            zone: Darkness zone classification
            
        Returns:
            RGBA color string for chart background
        """
        zone_colors = {
            "day": "rgba(255, 255, 0, 0.1)",              # Light yellow
            "civil_twilight": "rgba(255, 165, 0, 0.15)",   # Light orange
            "nautical_twilight": "rgba(255, 99, 71, 0.2)", # Light red/orange
            "astronomical_twilight": "rgba(75, 0, 130, 0.25)", # Light indigo
            "night": "rgba(0, 0, 0, 0.3)",                # Light black
            "unknown": "rgba(128, 128, 128, 0.1)"         # Light gray
        }
        return zone_colors.get(zone, zone_colors["unknown"])
    
    def calculate_zones_for_timerange(self, start_time: datetime, end_time: datetime, 
                                    interval_minutes: int = 15) -> List[Dict]:
        """
        Calculate darkness zones for a time range.
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            interval_minutes: Interval between calculations in minutes
            
        Returns:
            List of dictionaries with time, zone, and color information
        """
        zones = []
        current_time = start_time
        
        while current_time <= end_time:
            zone = self.get_darkness_zone(current_time)
            color = self.get_zone_color(zone)
            sun_alt = self.get_sun_altitude(current_time)
            
            zones.append({
                'time': current_time,
                'zone': zone,
                'color': color,
                'timestamp': current_time.timestamp() * 1000,  # For JavaScript
                'sun_altitude': sun_alt  # For debugging
            })
            
            # Move to next interval
            from datetime import timedelta
            current_time += timedelta(minutes=interval_minutes)
        
        return zones