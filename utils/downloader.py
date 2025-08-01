import yt_dlp
import os
import tempfile
import subprocess
import re
from pathlib import Path
import threading
import time

class YouTubeDownloader:
    def __init__(self):
        self.ydl_opts_base = {
            'quiet': True,
            'no_warnings': True,
            'extractaudio': False,
            'audioformat': 'best',
            'outtmpl': '%(title)s.%(ext)s',
            'restrictfilenames': True,
        }
    
    def get_video_info(self, url):
        """Extract video information without downloading"""
        try:
            ydl_opts = {
                **self.ydl_opts_base,
                'quiet': False,
                'no_warnings': False,
                'socket_timeout': 30,
                'retries': 3,
                'noplaylist': True,  # Only single video
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False) or {}
                
                # Extract relevant information
                video_info = {
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'duration_string': self._format_duration(info.get('duration', 0)),
                    'uploader': info.get('uploader', 'Unknown'),
                    'view_count': info.get('view_count', 0),
                    'thumbnail': info.get('thumbnail', ''),
                    'formats': info.get('formats', []),
                    'description': info.get('description', ''),
                    'upload_date': info.get('upload_date', ''),
                    'webpage_url': info.get('webpage_url', url)
                }
                
                return video_info
                
        except Exception as e:
            print(f"Error getting video info: {str(e)}")
            return None
    
    def download_video(self, url, output_dir, format_id=None, progress_callback=None):
        """Download video with specified format and convert to WhatsApp-compatible MP4"""
        try:
            # Create progress hook
            def progress_hook(d):
                if progress_callback:
                    progress_data = {}
                    if d['status'] == 'downloading':
                        if 'total_bytes' in d and 'downloaded_bytes' in d:
                            percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                            progress_data['percent'] = percent
                        elif '_percent_str' in d:
                            percent_str = d['_percent_str'].strip('%')
                            if percent_str.replace('.', '').isdigit():
                                progress_data['percent'] = float(percent_str)
                    
                    progress_data['status'] = d['status']
                    progress_callback(progress_data)
            
            # Configure download options
            ydl_opts = {
                **self.ydl_opts_base,
                'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
                'progress_hooks': [progress_hook],
                'socket_timeout': 30,
                'retries': 3,
                'quiet': False,
                'no_warnings': False,
                'noplaylist': True,  # Only single video
            }
            
            # Set format if specified
            if format_id:
                # Use format that works with ffmpeg for merging
                ydl_opts['format'] = f"{format_id}+bestaudio/best"
            else:
                ydl_opts['format'] = 'best'
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Get info first to determine output filename
                info = ydl.extract_info(url, download=False)
                if not info:
                    raise Exception("Failed to extract video info. The video may be unavailable or the URL is invalid.")
                title = self._sanitize_filename(info.get('title', 'video'))
                
                # Download the video
                ydl.download([url])
                
                # Find the downloaded file
                downloaded_file = self._find_downloaded_file(output_dir, title)
                return downloaded_file
                
        except Exception as e:
            print(f"Error downloading video: {str(e)}")
            return None

    def convert_to_whatsapp_mp4(self, input_path):
        """Convert a video to WhatsApp-compatible MP4 (H.264/AAC, max 720p) using ffmpeg"""
        try:
            output_path = os.path.splitext(input_path)[0] + '_whatsapp.mp4'
            # ffmpeg command: re-encode to H.264/AAC, max 720p
            cmd = [
                'ffmpeg', '-y', '-i', input_path,
                '-vf', 'scale=w=1280:h=720:force_original_aspect_ratio=decrease',
                '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
                '-c:a', 'aac', '-b:a', '128k',
                '-movflags', '+faststart',
                output_path
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return output_path if os.path.exists(output_path) else None
        except Exception as e:
            print(f"Error converting to WhatsApp MP4: {str(e)}")
            return None
    
    def download_audio(self, url, output_dir, audio_format='mp3', quality='best', progress_callback=None):
        """Download audio only with specified format and quality"""
        try:
            # Create progress hook
            def progress_hook(d):
                if progress_callback:
                    progress_data = {}
                    if d['status'] == 'downloading':
                        if 'total_bytes' in d and 'downloaded_bytes' in d:
                            percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                            progress_data['percent'] = percent
                        elif '_percent_str' in d:
                            percent_str = d['_percent_str'].strip('%')
                            if percent_str.replace('.', '').isdigit():
                                progress_data['percent'] = float(percent_str)
                    
                    progress_data['status'] = d['status']
                    progress_callback(progress_data)
            
            # Configure audio download options
            ydl_opts = {
                **self.ydl_opts_base,
                'format': 'bestaudio/best',
                'extractaudio': True,
                'audioformat': audio_format,
                'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
                'progress_hooks': [progress_hook],
                'socket_timeout': 30,
                'retries': 3,
                'quiet': False,
                'no_warnings': False,
                'noplaylist': True,  # Only single video
            }
            
            # Set audio quality
            if quality != 'best' and quality != 'Best Available':
                if quality.endswith('kbps'):
                    bitrate = quality.replace('kbps', '')
                    ydl_opts['audioquality'] = bitrate
            
            # Add postprocessor for audio conversion
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': audio_format,
                'preferredquality': quality.replace('kbps', '') if quality.endswith('kbps') else '192',
            }]
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Get info first to determine output filename
                info = ydl.extract_info(url, download=False)
                if not info:
                    raise Exception("Failed to extract video info. The video may be unavailable or the URL is invalid.")
                title = self._sanitize_filename(info.get('title', 'audio'))
                
                # Download the audio
                ydl.download([url])
                
                # Find the downloaded file
                downloaded_file = self._find_downloaded_file(output_dir, title, audio_format)
                return downloaded_file
                
        except Exception as e:
            print(f"Error downloading audio: {str(e)}")
            return None
    
    def add_branding_to_video(self, main_video_path, intro_path, outro_path):
        """Concatenate intro, main, and outro videos into a single file using ffmpeg concat filter, re-encoding to ensure audio."""
        try:
            temp_dir = os.path.dirname(main_video_path)
            final_path = os.path.splitext(main_video_path)[0] + '_branded.mp4'
            # Build input list and filter
            input_files = []
            filter_parts = []
            idx = 0
            for path in [intro_path, main_video_path, outro_path]:
                if path and os.path.exists(path):
                    input_files.extend(['-i', os.path.abspath(path)])
                    filter_parts.append(f'[{idx}:v:0][{idx}:a:0]')
                    idx += 1
            filter_complex = ''.join(filter_parts) + f'concat=n={idx}:v=1:a=1[outv][outa]'
            cmd = [
                'ffmpeg', '-y', *input_files,
                '-filter_complex', filter_complex,
                '-map', '[outv]', '-map', '[outa]',
                '-c:v', 'libx264', '-c:a', 'aac', '-b:a', '128k',
                '-movflags', '+faststart',
                final_path
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return final_path if os.path.exists(final_path) else None
        except Exception as e:
            print(f"Error adding branding: {str(e)}")
            return None
    
    def _format_duration(self, duration):
        """Format duration in seconds to HH:MM:SS"""
        if not duration:
            return "Unknown"
        
        hours = duration // 3600
        minutes = (duration % 3600) // 60
        seconds = duration % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def _sanitize_filename(self, filename):
        """Sanitize filename for filesystem compatibility"""
        # Remove/replace problematic characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = re.sub(r'\s+', ' ', filename)  # Replace multiple spaces with single space
        filename = filename.strip()
        
        # Limit length
        if len(filename) > 100:
            filename = filename[:100]
        
        return filename
    
    def _find_downloaded_file(self, directory, title, extension=None):
        """Find the downloaded file in the directory"""
        try:
            # Look for files with the title
            for file in os.listdir(directory):
                if title.lower() in file.lower():
                    if extension:
                        if file.lower().endswith(f'.{extension.lower()}'):
                            return os.path.join(directory, file)
                    else:
                        return os.path.join(directory, file)
            
            # If specific search fails, return the first file in directory
            files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
            if files:
                return os.path.join(directory, files[0])
            
            return None
            
        except Exception as e:
            print(f"Error finding downloaded file: {str(e)}")
            return None
    
    def get_available_formats(self, url):
        """Get all available formats for a video"""
        try:
            ydl_opts = {
                **self.ydl_opts_base,
                'listformats': True,
                'noplaylist': True,  # Only single video
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False) or {}
                return info.get('formats', [])
                
        except Exception as e:
            print(f"Error getting formats: {str(e)}")
            return []

def search_youtube(query, max_results=5):
    """
    Search YouTube using yt-dlp and return a list of video entries.
    """
    import yt_dlp
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'extract_flat': True,
        'noplaylist': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
            if info and isinstance(info, dict):
                return info.get('entries', [])
            else:
                return []
    except Exception as e:
        print(f"Search failed: {e}")
        return []
