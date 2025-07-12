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


# Initialize session state
if 'download_progress' not in st.session_state:
    st.session_state['download_progress'] = 0
if 'download_status' not in st.session_state:
    st.session_state['download_status'] = ""
if 'download_complete' not in st.session_state:
    st.session_state['download_complete'] = False
if 'video_info' not in st.session_state:
    st.session_state['video_info'] = None
if 'download_path' not in st.session_state:
    st.session_state['download_path'] = None

# Branding and header box with sticker
st.markdown(
    """
    <style>
    .header-box {
        position: relative;
        background: #fff;
        border: 2px solid #eee;
        border-radius: 12px;
        box-shadow: 0 2px 16px #eee;
        padding: 2.5em 2em 1.5em 2em;
        margin: 2em auto 2.5em auto;
        max-width: 600px;
        text-align: center;
    }
    .vibe-coder-sticker {
        position: absolute;
        top: -1.2em;
        right: 1.5em;
        background: #FF0000;
        color: #fff;
        padding: 0.3em 1.1em;
        border-radius: 8px;
        font-weight: bold;
        font-size: 1.1em;
        box-shadow: 0 2px 8px #ccc;
        z-index: 2;
        letter-spacing: 0.5px;
    }
    </style>
    <div class="header-box">
        <div class="vibe-coder-sticker">The Vibe Coder</div>
        <h1 style='margin-bottom:0.2em;'>🎥 YouTube Video & Shorts Downloader</h1>
        <div style='color:#444;margin-bottom:0.5em;'>
            Download YouTube videos and shorts with customizable quality options and audio formats.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("""
    <style>
    button[data-testid="stCodeCopyButton"] {
        background-color: #FF0000 !important;
        color: white !important;
        border-radius: 6px !important;
        padding: 0.25em 0.5em !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2) !important;
        transition: background 0.3s ease;
    }

    button[data-testid="stCodeCopyButton"]:hover {
        background-color: #cc0000 !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
    }
    </style>
""", unsafe_allow_html=True)

def main():
    # --- YouTube Search Section ---
    st.header("🔎 Search YouTube Video")
    if 'search_results' not in st.session_state:
        st.session_state['search_results'] = []
    if 'search_query' not in st.session_state:
        st.session_state['search_query'] = ''

    def on_search_entered():
        search_query = st.session_state['yt_search_input']
        if isinstance(search_query, str) and search_query.strip():
            try:
                from utils.downloader import search_youtube
                results = search_youtube(search_query, max_results=5)
                st.session_state['search_results'] = results
                st.session_state['search_query'] = search_query
            except Exception as e:
                st.error(f"Search failed: {e}")
                st.session_state['search_results'] = []

    search_query = st.text_input(
        "Search for a video",
        value=st.session_state['search_query'],
        key="yt_search_input",
        on_change=on_search_entered
    )
    search_btn = st.button("Search", key="yt_search_btn")
    if search_btn:
        on_search_entered()
    # Show search results
    if st.session_state['search_results']:
        st.markdown("**Select a video below:**")
        for i, entry in enumerate(st.session_state['search_results']):
            cols = st.columns([1, 4, 3])
            with cols[0]:
                thumb_url = entry.get('thumbnail')
                if not thumb_url and 'thumbnails' in entry and isinstance(entry['thumbnails'], list) and entry['thumbnails']:
                    # Use the last thumbnail (usually the largest)
                    thumb_url = entry['thumbnails'][-1].get('url') if isinstance(entry['thumbnails'][-1], dict) else entry['thumbnails'][-1]
                if thumb_url and thumb_url.startswith("//"):
                    thumb_url = "https:" + thumb_url
                if thumb_url:
                    st.image(thumb_url, width=100)
            with cols[1]:
                st.markdown(f"**{entry.get('title', 'No Title')}**")
                st.caption(entry.get('uploader', ''))
            with cols[2]:
                video_url = entry.get('url', '')
                cols_code, cols_btn = st.columns([8, 1])
                with cols_code:
                    st.code(video_url)
                with cols_btn:
                    st.markdown(f"""
                        <a href=\"{video_url}\" target=\"_blank\"
                           style=\"display:inline-flex;align-items:center;justify-content:center;background:none;width:2em;height:2em;border-radius:6px;text-decoration:none;\"
                           title=\"Show on youtube.com\">
                            <svg width=\"1.5em\" height=\"1.5em\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\">
                              <rect width=\"24\" height=\"24\" rx=\"6\" fill=\"#FF0000\"/>
                              <polygon points=\"10,8 16,12 10,16\" fill=\"white\"/>
                            </svg>
                        </a>
                    """, unsafe_allow_html=True)
    # --- End YouTube Search Section ---

    # URL Input Section
    st.header("📋 Enter YouTube URL")
    def on_url_entered():
        st.session_state['start_download'] = True
    url_default = st.session_state.get('url_from_search', '')
    url = st.text_input(
        "YouTube URL",
        value=url_default,
        placeholder="https://www.youtube.com/watch?v=example or https://youtube.com/shorts/example",
        help="Enter a valid YouTube video or shorts URL",
        on_change=on_url_entered,
        key="yt_url_input"
    )
    if 'url_from_search' in st.session_state:
        del st.session_state['url_from_search']
    download_type = st.radio(
        "Type",
        ["Video + Audio", "Audio Only"],
        horizontal=True,
        help="Choose whether to download video with audio or audio only"
    )
    do_not_confirm = st.checkbox("Auto Download", value=False, help="If checked, download starts automatically after video info loads.")

    # Download button
    download_btn_clicked = st.button("Fetch Video Info", type="primary", use_container_width=True, key="main_download_btn")
    if download_btn_clicked:
        st.session_state['start_download'] = True

    # Set default file location
    default_save_location = str(Path.home() / "Downloads")
    if 'save_location' not in st.session_state or st.session_state.get('save_location') is None:
        st.session_state['save_location'] = default_save_location

    # URL Validation and Video Info
    proceed_to_download = False
    if do_not_confirm and url:
        proceed_to_download = True
    elif st.session_state.get('start_download', False) and url:
        proceed_to_download = True

    if proceed_to_download:
        validation_result = validate_youtube_url(url)
        if validation_result['valid']:
            st.success("✅ Valid YouTube URL detected!")
            # Get video information automatically
            with st.spinner("Fetching video information..."):
                downloader = YouTubeDownloader()
                video_info = downloader.get_video_info(url)
                if video_info:
                    st.session_state['video_info'] = video_info
                else:
                    st.error("❌ Failed to fetch video information. Please check the URL.")
        else:
            st.error(f"❌ {validation_result['error']}")
        # Reset the button flag so user can click again for a new download
        st.session_state['start_download'] = False

    # Display Video Information and Download Options
    if st.session_state.get('video_info'):
        video_info = st.session_state['video_info']
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
        # Save Location Input
        st.session_state['save_location'] = st.text_input(
            "Save Location",
            value=st.session_state['save_location'],
            help="Specify the folder where the downloaded file will be saved."
        )
        # Video Quality Selection
        selected_video_format = None
        convert_to_whatsapp = False
        if download_type == "Video + Audio":
            st.subheader("🎬 Video Quality")
            available_formats = video_info.get('formats', [])
            # Group by resolution (height), pick best (largest filesize, or best vcodec)
            best_formats = {}
            for fmt in available_formats:
                if fmt.get('vcodec') != 'none' and fmt.get('height'):
                    height = fmt.get('height')
                    filesize = fmt.get('filesize') or 0
                    vcodec = fmt.get('vcodec', '')
                    ext = fmt.get('ext', '')
                    key = height
                    if key not in best_formats or (filesize > (best_formats[key].get('filesize') or 0)):
                        best_formats[key] = fmt
            # Prepare dropdown options, sorted by height descending
            sorted_heights = sorted(best_formats.keys(), reverse=True)
            video_formats = []
            for height in sorted_heights:
                fmt = best_formats[height]
                label = f"{height}p"
                if fmt.get('fps', 30) > 30:
                    label += f" {fmt.get('fps', 30)}fps"
                if fmt.get('filesize'):
                    size_mb = fmt['filesize'] / (1024 * 1024)
                    label += f" (~{size_mb:.1f}MB)"
                label += f" ({fmt.get('ext', '').upper()})"
                video_formats.append({
                    'label': label,
                    'format_id': fmt.get('format_id'),
                    'height': height,
                    'fps': fmt.get('fps', 30),
                    'filesize': fmt.get('filesize'),
                    'ext': fmt.get('ext', '')
                })
            if video_formats:
                video_quality_labels = [fmt['label'] for fmt in video_formats]
                default_index = 0  # Top-most (highest) resolution
                if 'video_quality' not in st.session_state:
                    st.session_state['video_quality'] = video_quality_labels[default_index]
                st.session_state['video_quality'] = st.selectbox(
                    "Select Video Quality",
                    video_quality_labels,
                    index=default_index,
                    help="Higher quality means larger file size",
                    key="video_quality_selectbox"
                )
                selected_video_format = next(fmt for fmt in video_formats if fmt['label'] == st.session_state['video_quality'])
                # WhatsApp conversion checkbox
                convert_to_whatsapp = st.checkbox("Convert to WhatsApp shareable format (MP4, 720p, H.264/AAC)", value=False, key="whatsapp_convert_checkbox")
                # Branding checkbox
                add_branding = st.checkbox("Add branding intro/outro (Vibe Coder)", value=False, key="branding_checkbox")
            else:
                st.error("No video formats available for this video.")
                return
        # Audio Options (only for audio-only downloads)
        if download_type == "Audio Only":
            st.subheader("🎵 Audio Options")
            audio_format = st.selectbox(
                "Audio Format",
                ["MP3", "AAC", "FLAC", "OGG"],
                help="Choose the audio format for download",
                key="audio_format_selectbox"
            )
            audio_quality = st.selectbox(
                "Audio Quality",
                ["Best Available", "320kbps", "192kbps", "128kbps"],
                help="Higher quality means larger file size",
                key="audio_quality_selectbox"
            )
        else:
            audio_format = "Best Available"
            audio_quality = "Best Available"
        # Download logic
        auto_download_triggered = False
        if do_not_confirm:
            if (
                (download_type == "Video + Audio" and selected_video_format) or
                (download_type == "Audio Only" and audio_format and audio_quality)
            ) and not st.session_state.get('auto_download_started', False):
                st.session_state['auto_download_started'] = True
                auto_download_triggered = True
        else:
            st.session_state['auto_download_started'] = False
        # Only proceed if selected_video_format is set for video
        if download_type == "Video + Audio" and not selected_video_format:
            st.error("No video format selected. Please select a video quality.")
        elif auto_download_triggered or (not do_not_confirm and st.button("Download", type="primary", use_container_width=True)):
            with st.spinner("Downloading, please wait..."):
                st.session_state['download_progress'] = 0
                st.session_state['download_status'] = "Starting download..."
                st.session_state['download_complete'] = False
                st.session_state['download_path'] = None
                def progress_callback(progress_data):
                    if 'percent' in progress_data:
                        percent = progress_data['percent']
                        if percent:
                            st.session_state['download_progress'] = min(percent, 100)
                            st.session_state['download_status'] = f"Downloading... {percent:.1f}%"
                    if 'status' in progress_data:
                        if progress_data['status'] == 'downloading':
                            st.session_state['download_status'] = "Downloading..."
                        elif progress_data['status'] == 'finished':
                            st.session_state['download_status'] = "Processing and finalizing..."
                downloader = YouTubeDownloader()
                file_manager = FileManager()
                temp_dir = file_manager.create_temp_directory()
                output_path = None
                try:
                    if download_type == "Video + Audio":
                        if not selected_video_format:
                            st.error("No video format selected. Please select a video quality.")
                            return
                        # Download video
                        output_path = downloader.download_video(
                            url,
                            temp_dir,
                            selected_video_format['format_id'],
                            progress_callback
                        )
                        # Optionally convert to WhatsApp format
                        if convert_to_whatsapp and output_path:
                            whatsapp_path = downloader.convert_to_whatsapp_mp4(output_path)
                            if whatsapp_path:
                                output_path = whatsapp_path
                        # Optionally add branding
                        if 'add_branding' in locals() and add_branding and output_path:
                            intro_path = 'intro.mp4'
                            outro_path = 'outro.mp4'
                            branded_path = downloader.add_branding_to_video(output_path, intro_path, outro_path)
                            if branded_path:
                                output_path = branded_path
                    else:
                        output_path = downloader.download_audio(
                            url,
                            temp_dir,
                            audio_format.lower(),
                            audio_quality,
                            progress_callback
                        )
                    # Move file to user-specified location
                    if output_path:
                        dest_folder = Path(st.session_state['save_location'])
                        dest_folder.mkdir(parents=True, exist_ok=True)
                        dest_path = dest_folder / Path(output_path).name
                        shutil.move(output_path, dest_path)
                        st.session_state['download_path'] = str(dest_path)
                        st.session_state['download_progress'] = 100
                        st.session_state['download_status'] = "Download completed!"
                        st.session_state['download_complete'] = True
                    else:
                        st.session_state['download_status'] = "Download failed!"
                        st.session_state['download_progress'] = 0
                except Exception as e:
                    st.session_state['download_status'] = f"Error: {str(e)}"
                    st.session_state['download_progress'] = 0
        # Show download status and file path
        if st.session_state['download_complete'] and st.session_state['download_path']:
            st.success("✅ Download completed successfully!")
            file_path = st.session_state['download_path']
            # Show file path with WhatsApp share instructions
            col_fp, col_wa = st.columns([8, 1])
            with col_fp:
                st.code(file_path, language="text")
            with col_wa:
                st.markdown(f'''
                    <a href="https://web.whatsapp.com/" target="_blank" style="display:inline-block;background:#25D366;padding:0.5em 1.2em;border-radius:6px;color:#fff;font-weight:bold;font-size:1.05em;box-shadow:0 2px 8px #ccc;text-decoration:none;width:100%;max-width:100%;min-width:0;box-sizing:border-box;text-align:center;" title="Open WhatsApp Web">
                        <span style="vertical-align:middle;">🟢</span>
                    </a>
                ''', unsafe_allow_html=True)
            # Video preview if file is a video
            video_exts = [".mp4", ".webm", ".mkv", ".mov", ".avi"]
            if any(file_path.lower().endswith(ext) for ext in video_exts):
                st.markdown("**Preview:**")
                st.video(file_path)
            # Audio preview if file is audio
            audio_exts = [".mp3", ".aac", ".flac", ".ogg", ".wav", ".m4a"]
            if any(file_path.lower().endswith(ext) for ext in audio_exts):
                st.markdown("**Audio Preview:**")
                st.audio(file_path)
            if st.button("🔄 Download Another Video", use_container_width=True, key="download_another"):
                reset_session_state()
                st.rerun()

def start_video_download(url, video_format, audio_format, audio_quality):
    """Start video download"""
    try:
        st.session_state['download_progress'] = 1
        st.session_state['download_status'] = "Starting download..."
        st.session_state['download_complete'] = False
        
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
                    st.session_state['download_progress'] = min(percent, 100)
                    st.session_state['download_status'] = f"Downloading... {percent:.1f}%"
            
            if 'status' in progress_data:
                if progress_data['status'] == 'downloading':
                    st.session_state['download_status'] = "Downloading video..."
                elif progress_data['status'] == 'finished':
                    st.session_state['download_status'] = "Processing and finalizing..."
        
        # Download video
        output_path = downloader.download_video(
            url, 
            temp_dir, 
            video_format['format_id'],
            progress_callback
        )
        
        if output_path:
            st.session_state['download_path'] = output_path
            st.session_state['download_progress'] = 100
            st.session_state['download_status'] = "Download completed!"
            st.session_state['download_complete'] = True
        else:
            st.session_state['download_status'] = "Download failed!"
            st.session_state['download_progress'] = 0
            
    except Exception as e:
        st.session_state['download_status'] = f"Error: {str(e)}"
        st.session_state['download_progress'] = 0

def start_audio_download(url, audio_format, audio_quality):
    """Start audio download"""
    try:
        st.session_state['download_progress'] = 1
        st.session_state['download_status'] = "Starting audio download..."
        st.session_state['download_complete'] = False
        
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
                    st.session_state['download_progress'] = min(percent, 100)
                    st.session_state['download_status'] = f"Downloading... {percent:.1f}%"
            
            if 'status' in progress_data:
                if progress_data['status'] == 'downloading':
                    st.session_state['download_status'] = "Downloading audio..."
                elif progress_data['status'] == 'finished':
                    st.session_state['download_status'] = "Processing and converting..."
        
        # Download audio
        output_path = downloader.download_audio(
            url, 
            temp_dir, 
            audio_format.lower(),
            audio_quality,
            progress_callback
        )
        
        if output_path:
            st.session_state['download_path'] = output_path
            st.session_state['download_progress'] = 100
            st.session_state['download_status'] = "Download completed!"
            st.session_state['download_complete'] = True
        else:
            st.session_state['download_status'] = "Download failed!"
            st.session_state['download_progress'] = 0
            
    except Exception as e:
        st.session_state['download_status'] = f"Error: {str(e)}"
        st.session_state['download_progress'] = 0

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
    st.session_state['download_progress'] = 0
    st.session_state['download_status'] = ""
    st.session_state['download_complete'] = False
    st.session_state['video_info'] = None
    st.session_state['download_path'] = None

if __name__ == "__main__":
    main()
