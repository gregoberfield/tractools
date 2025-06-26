import threading
import time
import requests
import subprocess
import os
import tempfile
import logging
import shutil
from datetime import datetime
from config import Config
from module_manager import ModuleManager

logger = logging.getLogger(__name__)

class ImageStreamerTool:
    """Service for scraping images and streaming them via RTSP"""
    
    def __init__(self):
        self.streams = {}
        self.config = None
        self.running = False
        self.threads = {}
        self.temp_dir = tempfile.mkdtemp(prefix='image_streamer_')
        self.ffmpeg_path = None
        
    def start(self):
        """Start the image streamer service"""
        logger.info("Starting Image Streamer Tool")
        
        # Check FFmpeg availability first
        if not self._check_ffmpeg():
            logger.error("FFmpeg is not available. Cannot start streaming service.")
            return False
            
        self.running = True
        self.load_config()
        self._start_configured_streams()
        return True
        
    def stop(self):
        """Stop the image streamer service"""
        logger.info("Stopping Image Streamer Tool")
        self.running = False
        for stream_name in list(self.streams.keys()):
            self.stop_stream(stream_name)
            
    def _check_ffmpeg(self):
        """Check if FFmpeg is available and working"""
        possible_paths = [
            'ffmpeg',                    # System PATH
            '/usr/bin/ffmpeg',           # Standard apt installation
            '/snap/bin/ffmpeg',          # Snap installation
            '/usr/local/bin/ffmpeg',     # Compiled from source
        ]
        
        for path in possible_paths:
            try:
                if path == 'ffmpeg':
                    # Check if it's in PATH
                    if shutil.which('ffmpeg'):
                        result = subprocess.run([path, '-version'], 
                                              stdout=subprocess.PIPE, 
                                              stderr=subprocess.PIPE, 
                                              check=True, 
                                              timeout=5)
                        self.ffmpeg_path = path
                        logger.info(f"Found working FFmpeg at: {path}")
                        return True
                else:
                    # Check specific path
                    if os.path.exists(path) and os.access(path, os.X_OK):
                        result = subprocess.run([path, '-version'], 
                                              stdout=subprocess.PIPE, 
                                              stderr=subprocess.PIPE, 
                                              check=True, 
                                              timeout=5)
                        self.ffmpeg_path = path
                        logger.info(f"Found working FFmpeg at: {path}")
                        return True
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, 
                    FileNotFoundError, PermissionError) as e:
                logger.debug(f"FFmpeg not working at {path}: {e}")
                continue
        
        logger.error("FFmpeg not found or not working. Please install with: sudo apt install ffmpeg")
        return False
        
    def load_config(self):
        """Load configuration from JSON file"""
        try:
            self.config = Config.load_streams_config()
            logger.info(f"Loaded configuration with {len(self.config['streams'])} streams")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
            
    def reload_config(self):
        """Reload configuration and restart streams"""
        try:
            old_streams = set(self.streams.keys())
            self.load_config()
            
            # Stop removed streams
            new_stream_names = {s['name'] for s in self.config['streams']}
            for stream_name in old_streams - new_stream_names:
                self.stop_stream(stream_name)
                
            # Start new/updated streams
            self._start_configured_streams()
            
            return {'status': 'success', 'message': 'Configuration reloaded'}
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
            return {'status': 'error', 'message': str(e)}
            
    def _start_configured_streams(self):
        """Start all enabled streams from configuration"""
        for stream_config in self.config['streams']:
            if stream_config.get('enabled', True):
                self.start_stream(stream_config['name'])
                
    def start_stream(self, stream_name):
        """Start a specific stream"""
        if not self.ffmpeg_path:
            return {'status': 'error', 'message': 'FFmpeg not available'}
            
        if stream_name in self.streams:
            return {'status': 'info', 'message': 'Stream already running'}
            
        # Find stream config
        stream_config = None
        for config in self.config['streams']:
            if config['name'] == stream_name:
                stream_config = config
                break
                
        if not stream_config:
            return {'status': 'error', 'message': 'Stream not found in configuration'}
            
        try:
            # Create stream data structure
            stream_data = {
                'config': stream_config,
                'status': 'starting',
                'last_update': None,
                'error_count': 0,
                'ffmpeg_process': None
            }
            
            self.streams[stream_name] = stream_data
            
            # Start the streaming thread
            thread = threading.Thread(
                target=self._stream_worker,
                args=(stream_name,),
                daemon=True
            )
            thread.start()
            self.threads[stream_name] = thread
            
            logger.info(f"Started stream: {stream_name}")
            return {'status': 'success', 'message': f'Stream {stream_name} started'}
            
        except Exception as e:
            logger.error(f"Failed to start stream {stream_name}: {e}")
            if stream_name in self.streams:
                del self.streams[stream_name]
            return {'status': 'error', 'message': str(e)}
            
    def stop_stream(self, stream_name):
        """Stop a specific stream"""
        if stream_name not in self.streams:
            return {'status': 'info', 'message': 'Stream not running'}
            
        try:
            stream_data = self.streams[stream_name]
            
            # Kill FFmpeg process if running
            if stream_data.get('ffmpeg_process'):
                try:
                    stream_data['ffmpeg_process'].terminate()
                    stream_data['ffmpeg_process'].wait(timeout=5)
                except subprocess.TimeoutExpired:
                    stream_data['ffmpeg_process'].kill()
                    stream_data['ffmpeg_process'].wait(timeout=2)
                except Exception as e:
                    logger.warning(f"Error stopping FFmpeg process for {stream_name}: {e}")
                
            # Remove from active streams
            del self.streams[stream_name]
            
            logger.info(f"Stopped stream: {stream_name}")
            return {'status': 'success', 'message': f'Stream {stream_name} stopped'}
            
        except Exception as e:
            logger.error(f"Failed to stop stream {stream_name}: {e}")
            return {'status': 'error', 'message': str(e)}
            
    def _stream_worker(self, stream_name):
        """Worker thread for a single stream"""
        stream_data = self.streams[stream_name]
        config = stream_data['config']
        
        image_path = os.path.join(self.temp_dir, f"{stream_name}.jpg")
        
        while self.running and stream_name in self.streams:
            try:
                # Download image
                headers = {
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(config['url'], timeout=30, headers=headers)
                response.raise_for_status()
                
                # Save image
                with open(image_path, 'wb') as f:
                    f.write(response.content)
                    
                # Start/restart FFmpeg if needed
                if not stream_data.get('ffmpeg_process') or stream_data['ffmpeg_process'].poll() is not None:
                    self._start_ffmpeg(stream_name, image_path)
                    
                stream_data['status'] = 'running'
                stream_data['last_update'] = datetime.now().isoformat()
                stream_data['error_count'] = 0
                
                # Wait for next update
                time.sleep(config.get('update_frequency', 5))
                
            except Exception as e:
                stream_data['error_count'] += 1
                stream_data['status'] = f'error: {str(e)}'
                logger.error(f"Error in stream {stream_name}: {e}")
                
                # Back off on repeated errors
                backoff_time = min(30, 5 * stream_data['error_count'])
                logger.info(f"Backing off for {backoff_time} seconds due to errors")
                time.sleep(backoff_time)
                
    def _start_ffmpeg(self, stream_name, image_path):
        """Start FFmpeg process for RTSP streaming"""
        # Check if image_streamer module is enabled
        if not ModuleManager.is_module_enabled('image_streamer'):
            logger.info(f"Image streamer module is disabled. Skipping FFmpeg launch for stream {stream_name}")
            return
            
        stream_data = self.streams[stream_name]
        
        # Kill existing process
        if stream_data.get('ffmpeg_process'):
            try:
                stream_data['ffmpeg_process'].terminate()
                stream_data['ffmpeg_process'].wait(timeout=5)
            except:
                pass
        
        # Add authentication to RTSP URL
        publisher_url = f"rtsp://{Config.RTSP_PUBLISHER_USER}:{Config.RTSP_PUBLISHER_PASS}@localhost:{Config.RTSP_BASE_PORT}/{stream_name}"
        
        # FFmpeg command optimized for continuous static image streaming
        cmd = [
            self.ffmpeg_path,              # Use detected FFmpeg path
            '-loop', '1',                  # Loop the image indefinitely
            '-re',                         # Read input at native frame rate
            '-i', image_path,              # Input image
            '-c:v', 'libx264',             # Video codec
            '-preset', 'ultrafast',        # Fast encoding
            '-tune', 'stillimage',         # Optimize for still images
            '-pix_fmt', 'yuv420p',         # Pixel format
            '-r', '5',                     # 5 fps (higher for better streaming)
            '-g', '25',                    # GOP size (keyframe every 5 seconds)
            '-keyint_min', '5',            # Minimum keyframe interval
            '-sc_threshold', '0',          # Disable scene change detection
            '-fflags', '+genpts',          # Generate presentation timestamps
            '-avoid_negative_ts', 'make_zero',  # Handle timestamps
            '-f', 'rtsp',                  # Output format
            '-rtsp_transport', 'tcp',      # Use TCP for RTSP
            '-buffer_size', '64k',         # Small buffer
            '-max_delay', '500000',        # 0.5 second max delay
            publisher_url                  # Use authenticated URL
        ]
        
        try:
            # Start FFmpeg process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                preexec_fn=os.setsid  # Create new process group
            )
            stream_data['ffmpeg_process'] = process
            logger.info(f"Started FFmpeg for stream {stream_name} -> rtsp://localhost:{Config.RTSP_BASE_PORT}/{stream_name}")
            
            # Check if process started successfully
            time.sleep(1)
            if process.poll() is not None:
                # Process died immediately, log error
                stdout, stderr = process.communicate()
                logger.error(f"FFmpeg failed to start for {stream_name}: {stderr.decode()}")
                
        except Exception as e:
            logger.error(f"Failed to start FFmpeg for {stream_name}: {e}")
            
    def get_status(self):
        """Get status of all streams"""
        ffmpeg_status = "Available" if self.ffmpeg_path else "Not Available"
        
        return {
            'service_running': self.running,
            'ffmpeg_status': ffmpeg_status,
            'ffmpeg_path': self.ffmpeg_path,
            'active_streams': len(self.streams),
            'streams': {
                name: {
                    'status': data['status'],
                    'last_update': data['last_update'],
                    'error_count': data['error_count'],
                    'rtsp_url': f"rtsp://{Config.RTSP_VIEWER_USER}:{Config.RTSP_VIEWER_PASS}@localhost:{Config.RTSP_BASE_PORT}/{name}"
                }
                for name, data in self.streams.items()
            }
        }
        
    def list_streams(self):
        """List all configured streams"""
        if not self.config:
            return {'streams': []}
            
        return {
            'streams': [
                {
                    'name': stream['name'],
                    'url': stream['url'],
                    'update_frequency': stream.get('update_frequency', 5),
                    'enabled': stream.get('enabled', True),
                    'running': stream['name'] in self.streams,
                    'rtsp_url': f"rtsp://{Config.RTSP_VIEWER_USER}:{Config.RTSP_VIEWER_PASS}@localhost:{Config.RTSP_BASE_PORT}/{stream['name']}"
                }
                for stream in self.config['streams']
            ]
        }