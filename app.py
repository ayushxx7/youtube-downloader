import streamlit as st
import os
import tempfile
import shutil
from pathlib import Path
import time
import threading
from utils.downloader import YouTubeDownloader
from utils.validators import validate_youtube_url
from utils.file_manager import FileManager

# Configure page
st.set_page_config(
    page_title="YouTube Downloader",
    page_icon="🎥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if 'download_progress' not in st.session_state:
    st.session_state.download_progress = 0
if 'download_status' not in st.session_state:
    st.session_state.download_status = ""
if 'download_complete' not in st.session_state:
    st.session_state.download_complete = False
if 'video_info' not in st.session_state:
    st.session_state.video_info = None
if 'download_path' not in st.session_state:
    st.session_state.download_path = None

def main():
    st.title("🎥 YouTube Video & Shorts Downloader")
    st.markdown("Download YouTube videos and shorts with customizable quality options and audio formats.")
    
    # URL Input Section
    st.header("📋 Enter YouTube URL")
    url = st.text_input(
        "YouTube URL",
        placeholder="https://www.youtube.com/watch?v=example or https://youtube.com/shorts/example",
        help="Enter a valid YouTube video or shorts URL"
    )
    
    # URL Validation and Video Info
    if url:
        validation_result = validate_youtube_url(url)
        if validation_result['valid']:
            st.success("✅ Valid YouTube URL detected!")
            
            # Get video information
            if st.button("🔍 Get Video Info", type="primary"):
                with st.spinner("Fetching video information..."):
                    downloader = YouTubeDownloader()
                    video_info = downloader.get_video_info(url)
                    
                    if video_info:
                        st.session_state.video_info = video_info
                        st.rerun()
                    else:
                        st.error("❌ Failed to fetch video information. Please check the URL.")
        else:
            st.error(f"❌ {validation_result['error']}")
    
    # Display Video Information and Download Options
    if st.session_state.video_info:
        video_info = st.session_state.video_info
        
        # Video Information Display
        st.header("📺 Video Information")
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if video_info.get('thumbnail'):
                st.image(video_info['thumbnail'], width=200)
        
        with col2:
            st.markdown(f"**Title:** {video_info.get('title', 'N/A')}")
            st.markdown(f"**Duration:** {video_info.get('duration_string', 'N/A')}")
            st.markdown(f"**Uploader:** {video_info.get('uploader', 'N/A')}")
            st.markdown(f"**Views:** {video_info.get('view_count', 'N/A'):,}" if video_info.get('view_count') else "**Views:** N/A")
        
        # Download Options
        st.header("⚙️ Download Options")
        
        # Download Type Selection
        download_type = st.selectbox(
            "Download Type",
            ["Video + Audio", "Audio Only"],
            help="Choose whether to download video with audio or audio only"
        )
        
        if download_type == "Video + Audio":
            # Video Quality Selection
            st.subheader("🎬 Video Quality")
            available_formats = video_info.get('formats', [])
            
            # Filter and organize video formats
            video_formats = []
            for fmt in available_formats:
                if fmt.get('vcodec') != 'none' and fmt.get('height'):
                    height = fmt.get('height')
                    fps = fmt.get('fps', 30)
                    filesize = fmt.get('filesize')
                    
                    quality_label = f"{height}p"
                    if fps and fps > 30:
                        quality_label += f" {fps}fps"
                    if filesize:
                        size_mb = filesize / (1024 * 1024)
                        quality_label += f" (~{size_mb:.1f}MB)"
                    
                    video_formats.append({
                        'label': quality_label,
                        'format_id': fmt.get('format_id'),
                        'height': height,
                        'fps': fps or 30,
                        'filesize': filesize
                    })
            
            # Sort by quality (height) descending
            video_formats.sort(key=lambda x: x['height'], reverse=True)
            
            if video_formats:
                video_quality = st.selectbox(
                    "Select Video Quality",
                    [fmt['label'] for fmt in video_formats],
                    help="Higher quality means larger file size"
                )
                selected_video_format = next(fmt for fmt in video_formats if fmt['label'] == video_quality)
            else:
                st.error("No video formats available for this video.")
                return
        
        # Audio Options (only for audio-only downloads)
        if download_type == "Audio Only":
            st.subheader("🎵 Audio Options")
            
            audio_format = st.selectbox(
                "Audio Format",
                ["MP3", "AAC", "FLAC", "OGG"],
                help="Choose the audio format for download"
            )
            
            audio_quality = st.selectbox(
                "Audio Quality",
                ["Best Available", "320kbps", "192kbps", "128kbps"],
                help="Higher quality means larger file size"
            )
        else:
            audio_format = "Best Available"
            audio_quality = "Best Available"
        
        # Download Button
        st.header("📥 Download")
        
        if st.button("🚀 Start Download", type="primary", use_container_width=True):
            if download_type == "Video + Audio":
                start_video_download_thread(url, selected_video_format, audio_format, audio_quality)
            else:
                start_audio_download_thread(url, audio_format, audio_quality)
    
    # Download Progress
    if st.session_state.download_progress > 0:
        st.header("📊 Download Progress")
        
        progress_bar = st.progress(st.session_state.download_progress / 100)
        st.write(f"Status: {st.session_state.download_status}")
        
        if st.session_state.download_complete and st.session_state.download_path:
            st.success("✅ Download completed successfully!")
            
            # File download button
            if os.path.exists(st.session_state.download_path):
                with open(st.session_state.download_path, 'rb') as file:
                    file_data = file.read()
                    filename = os.path.basename(st.session_state.download_path)
                    
                    st.download_button(
                        label="💾 Download File",
                        data=file_data,
                        file_name=filename,
                        mime="application/octet-stream",
                        use_container_width=True
                    )
            
            # Reset button
            if st.button("🔄 Download Another Video", use_container_width=True):
                reset_session_state()
                st.rerun()

def start_video_download(url, video_format, audio_format, audio_quality):
    """Start video download"""
    try:
        st.session_state.download_progress = 1
        st.session_state.download_status = "Starting download..."
        st.session_state.download_complete = False
        
        # Show initial progress
        st.rerun()
        
        downloader = YouTubeDownloader()
        file_manager = FileManager()
        
        # Create temporary directory
        temp_dir = file_manager.create_temp_directory()
        
        # Progress callback
        def progress_callback(progress_data):
            if 'percent' in progress_data:
                percent = progress_data['percent']
                if percent:
                    st.session_state.download_progress = min(percent, 100)
                    st.session_state.download_status = f"Downloading... {percent:.1f}%"
            
            if 'status' in progress_data:
                if progress_data['status'] == 'downloading':
                    st.session_state.download_status = "Downloading video..."
                elif progress_data['status'] == 'finished':
                    st.session_state.download_status = "Processing and finalizing..."
        
        # Download video
        output_path = downloader.download_video(
            url, 
            temp_dir, 
            video_format['format_id'],
            progress_callback
        )
        
        if output_path:
            st.session_state.download_path = output_path
            st.session_state.download_progress = 100
            st.session_state.download_status = "Download completed!"
            st.session_state.download_complete = True
        else:
            st.session_state.download_status = "Download failed!"
            st.session_state.download_progress = 0
            
    except Exception as e:
        st.session_state.download_status = f"Error: {str(e)}"
        st.session_state.download_progress = 0

def start_audio_download(url, audio_format, audio_quality):
    """Start audio download"""
    try:
        st.session_state.download_progress = 1
        st.session_state.download_status = "Starting audio download..."
        st.session_state.download_complete = False
        
        # Show initial progress
        st.rerun()
        
        downloader = YouTubeDownloader()
        file_manager = FileManager()
        
        # Create temporary directory
        temp_dir = file_manager.create_temp_directory()
        
        # Progress callback
        def progress_callback(progress_data):
            if 'percent' in progress_data:
                percent = progress_data['percent']
                if percent:
                    st.session_state.download_progress = min(percent, 100)
                    st.session_state.download_status = f"Downloading... {percent:.1f}%"
            
            if 'status' in progress_data:
                if progress_data['status'] == 'downloading':
                    st.session_state.download_status = "Downloading audio..."
                elif progress_data['status'] == 'finished':
                    st.session_state.download_status = "Processing and converting..."
        
        # Download audio
        output_path = downloader.download_audio(
            url, 
            temp_dir, 
            audio_format.lower(),
            audio_quality,
            progress_callback
        )
        
        if output_path:
            st.session_state.download_path = output_path
            st.session_state.download_progress = 100
            st.session_state.download_status = "Download completed!"
            st.session_state.download_complete = True
        else:
            st.session_state.download_status = "Download failed!"
            st.session_state.download_progress = 0
            
    except Exception as e:
        st.session_state.download_status = f"Error: {str(e)}"
        st.session_state.download_progress = 0

def start_video_download_thread(url, video_format, audio_format, audio_quality):
    def download_task():
        start_video_download(url, video_format, audio_format, audio_quality)
    threading.Thread(target=download_task, daemon=True).start()

def start_audio_download_thread(url, audio_format, audio_quality):
    def download_task():
        start_audio_download(url, audio_format, audio_quality)
    threading.Thread(target=download_task, daemon=True).start()

def reset_session_state():
    """Reset all session state variables"""
    st.session_state.download_progress = 0
    st.session_state.download_status = ""
    st.session_state.download_complete = False
    st.session_state.video_info = None
    st.session_state.download_path = None

if __name__ == "__main__":
    main()
