import os
import tempfile
import shutil
from pathlib import Path
import time
import threading

class FileManager:
    def __init__(self):
        self.temp_directories = []
        self.cleanup_thread = None
        self.start_cleanup_thread()
    
    def create_temp_directory(self, prefix="youtube_download_"):
        """Create a temporary directory for downloads"""
        try:
            temp_dir = tempfile.mkdtemp(prefix=prefix)
            self.temp_directories.append({
                'path': temp_dir,
                'created': time.time()
            })
            return temp_dir
        except Exception as e:
            print(f"Error creating temp directory: {str(e)}")
            return None
    
    def cleanup_temp_directories(self, max_age_hours=24):
        """Clean up temporary directories older than max_age_hours"""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        directories_to_remove = []
        
        for temp_dir in self.temp_directories:
            if current_time - temp_dir['created'] > max_age_seconds:
                try:
                    if os.path.exists(temp_dir['path']):
                        shutil.rmtree(temp_dir['path'])
                    directories_to_remove.append(temp_dir)
                except Exception as e:
                    print(f"Error removing temp directory {temp_dir['path']}: {str(e)}")
        
        # Remove cleaned directories from tracking
        for temp_dir in directories_to_remove:
            self.temp_directories.remove(temp_dir)
    
    def start_cleanup_thread(self):
        """Start background thread for periodic cleanup"""
        def cleanup_worker():
            while True:
                try:
                    self.cleanup_temp_directories()
                    time.sleep(3600)  # Check every hour
                except Exception as e:
                    print(f"Error in cleanup thread: {str(e)}")
                    time.sleep(3600)
        
        if not self.cleanup_thread or not self.cleanup_thread.is_alive():
            self.cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
            self.cleanup_thread.start()
    
    def get_safe_filename(self, filename, max_length=100):
        """Generate a safe filename for the filesystem"""
        import re
        
        # Remove/replace problematic characters
        safe_filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        safe_filename = re.sub(r'\s+', ' ', safe_filename)  # Replace multiple spaces
        safe_filename = safe_filename.strip()
        
        # Limit length
        if len(safe_filename) > max_length:
            name, ext = os.path.splitext(safe_filename)
            available_length = max_length - len(ext)
            safe_filename = name[:available_length] + ext
        
        return safe_filename
    
    def get_file_size(self, file_path):
        """Get file size in bytes"""
        try:
            if os.path.exists(file_path):
                return os.path.getsize(file_path)
            return 0
        except Exception as e:
            print(f"Error getting file size: {str(e)}")
            return 0
    
    def get_file_size_human_readable(self, file_path):
        """Get file size in human-readable format"""
        size_bytes = self.get_file_size(file_path)
        
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def ensure_directory_exists(self, directory_path):
        """Ensure directory exists, create if it doesn't"""
        try:
            os.makedirs(directory_path, exist_ok=True)
            return True
        except Exception as e:
            print(f"Error creating directory {directory_path}: {str(e)}")
            return False
    
    def move_file(self, source_path, destination_path):
        """Move file from source to destination"""
        try:
            # Ensure destination directory exists
            destination_dir = os.path.dirname(destination_path)
            self.ensure_directory_exists(destination_dir)
            
            shutil.move(source_path, destination_path)
            return True
        except Exception as e:
            print(f"Error moving file from {source_path} to {destination_path}: {str(e)}")
            return False
    
    def copy_file(self, source_path, destination_path):
        """Copy file from source to destination"""
        try:
            # Ensure destination directory exists
            destination_dir = os.path.dirname(destination_path)
            self.ensure_directory_exists(destination_dir)
            
            shutil.copy2(source_path, destination_path)
            return True
        except Exception as e:
            print(f"Error copying file from {source_path} to {destination_path}: {str(e)}")
            return False
    
    def delete_file(self, file_path):
        """Delete a file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"Error deleting file {file_path}: {str(e)}")
            return False
    
    def list_files_in_directory(self, directory_path, extension=None):
        """List files in directory, optionally filtered by extension"""
        try:
            if not os.path.exists(directory_path):
                return []
            
            files = []
            for filename in os.listdir(directory_path):
                file_path = os.path.join(directory_path, filename)
                if os.path.isfile(file_path):
                    if extension is None or filename.lower().endswith(extension.lower()):
                        files.append(file_path)
            
            return files
        except Exception as e:
            print(f"Error listing files in {directory_path}: {str(e)}")
            return []
    
    def cleanup_on_exit(self):
        """Clean up all temporary directories on application exit"""
        for temp_dir in self.temp_directories:
            try:
                if os.path.exists(temp_dir['path']):
                    shutil.rmtree(temp_dir['path'])
            except Exception as e:
                print(f"Error cleaning up temp directory {temp_dir['path']}: {str(e)}")
        
        self.temp_directories.clear()
