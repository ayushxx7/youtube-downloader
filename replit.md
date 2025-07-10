# YouTube Downloader - Replit Project

## Overview

This is a Streamlit-based YouTube video and shorts downloader application that allows users to download YouTube content with customizable quality options and audio formats. The application uses yt-dlp for video extraction and provides a clean web interface for easy interaction.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit web framework
- **Interface**: Single-page application with centered layout
- **State Management**: Streamlit session state for tracking download progress, status, and video information
- **User Flow**: URL input → validation → video info display → download options → progress tracking

### Backend Architecture
- **Core Framework**: Python-based with modular utility structure
- **Video Processing**: yt-dlp library for YouTube video extraction and downloading
- **File Management**: Temporary directory system with automatic cleanup
- **Validation**: URL pattern matching for YouTube video/shorts URLs

### Data Storage Solutions
- **Temporary Storage**: Local temporary directories for downloaded files
- **Session Storage**: Streamlit session state for user interaction data
- **No Persistent Database**: Application operates with ephemeral storage only

## Key Components

### 1. Main Application (app.py)
- **Purpose**: Primary Streamlit interface and user interaction logic
- **Features**: URL input, progress tracking, download status management
- **Session State Management**: Tracks download progress, status, completion state, video info, and download paths

### 2. YouTube Downloader (utils/downloader.py)
- **Purpose**: Core video downloading functionality using yt-dlp
- **Features**: Video info extraction, format selection, download progress tracking
- **Configuration**: Flexible ydl_opts for different download scenarios

### 3. File Manager (utils/file_manager.py)
- **Purpose**: Temporary file and directory management
- **Features**: Automatic cleanup of old temporary directories, background cleanup threading
- **Cleanup Strategy**: Removes directories older than 24 hours via background thread

### 4. URL Validator (utils/validators.py)
- **Purpose**: YouTube URL validation and video ID extraction
- **Supported Formats**: Standard YouTube videos, YouTube Shorts, shortened URLs, mobile URLs, YouTube Music URLs
- **Validation**: Regex pattern matching with video ID format verification

## Data Flow

1. **User Input**: User enters YouTube URL in Streamlit interface
2. **URL Validation**: Validator checks URL format and extracts video ID
3. **Video Info Extraction**: Downloader retrieves video metadata without downloading
4. **Download Configuration**: User selects quality/format options
5. **Download Process**: yt-dlp downloads video to temporary directory
6. **Progress Tracking**: Real-time updates via Streamlit session state
7. **File Delivery**: Downloaded file made available for user download
8. **Cleanup**: Background thread removes old temporary files

## External Dependencies

### Core Libraries
- **streamlit**: Web interface framework
- **yt-dlp**: YouTube video downloading and extraction
- **pathlib**: Path manipulation utilities
- **tempfile**: Temporary file/directory creation
- **shutil**: File operations and cleanup
- **threading**: Background cleanup operations
- **re**: Regular expression pattern matching for URL validation
- **urllib.parse**: URL parsing utilities

### System Requirements
- Python 3.7+ environment
- Internet connectivity for YouTube access
- Sufficient disk space for temporary file storage

## Deployment Strategy

### Local Development
- **Setup**: Standard Python environment with pip requirements
- **Runtime**: Streamlit development server
- **File Storage**: Local temporary directories

### Production Considerations
- **Scalability**: Single-user focused design, may need session isolation for multi-user
- **Storage**: Temporary file cleanup essential for long-running deployments
- **Performance**: yt-dlp performance dependent on video size and network speed
- **Security**: URL validation prevents malicious input, temporary file isolation

### Replit Deployment
- **Environment**: Python repl with streamlit installation
- **Storage**: Replit's ephemeral file system suitable for temporary downloads
- **Networking**: Replit's internet access enables YouTube video fetching
- **Limitations**: Consider Replit's disk space and bandwidth limits for large video downloads

## Technical Decisions

### Why Streamlit?
- **Problem**: Need simple, fast web interface for video downloading
- **Solution**: Streamlit provides rapid prototyping with minimal web development overhead
- **Alternatives**: Flask/Django would require more frontend development
- **Pros**: Quick setup, built-in state management, easy deployment
- **Cons**: Limited customization, single-user sessions

### Why yt-dlp?
- **Problem**: Reliable YouTube video extraction and downloading
- **Solution**: yt-dlp is the most robust YouTube downloader library
- **Alternatives**: youtube-dl (less maintained), custom scraping (unreliable)
- **Pros**: Regular updates, format flexibility, metadata extraction
- **Cons**: External dependency, potential breaking changes with YouTube updates

### Why Temporary File System?
- **Problem**: Need storage for downloaded videos without persistent database
- **Solution**: Temporary directories with automatic cleanup
- **Alternatives**: Permanent storage, cloud storage, streaming delivery
- **Pros**: No database required, automatic cleanup, simple implementation
- **Cons**: Files lost on server restart, storage limitations