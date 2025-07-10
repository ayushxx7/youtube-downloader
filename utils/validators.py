import re
from urllib.parse import urlparse, parse_qs

def validate_youtube_url(url):
    """
    Validate if the provided URL is a valid YouTube video or shorts URL
    
    Args:
        url (str): The URL to validate
    
    Returns:
        dict: {'valid': bool, 'error': str, 'video_id': str}
    """
    
    if not url:
        return {'valid': False, 'error': 'URL cannot be empty'}
    
    # Remove whitespace
    url = url.strip()
    
    # YouTube URL patterns
    youtube_patterns = [
        # Standard YouTube video URLs
        r'^https?://(www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        r'^https?://(www\.)?youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})',
        
        # YouTube Shorts URLs
        r'^https?://(www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
        
        # Shortened YouTube URLs
        r'^https?://youtu\.be/([a-zA-Z0-9_-]{11})',
        
        # Mobile YouTube URLs
        r'^https?://m\.youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        r'^https?://m\.youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})',
        
        # YouTube Music URLs
        r'^https?://music\.youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        r'^https?://music\.youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})',
    ]
    
    # Check against each pattern
    for pattern in youtube_patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(2)
            
            # Additional validation for video ID
            if len(video_id) == 11 and re.match(r'^[a-zA-Z0-9_-]{11}$', video_id):
                return {
                    'valid': True,
                    'error': None,
                    'video_id': video_id,
                    'url_type': get_url_type(url)
                }
    
    # If no pattern matches, provide detailed error
    parsed_url = urlparse(url)
    
    if not parsed_url.scheme:
        return {'valid': False, 'error': 'URL must include http:// or https://'}
    
    if parsed_url.netloc.lower() not in ['www.youtube.com', 'youtube.com', 'youtu.be', 'm.youtube.com', 'music.youtube.com']:
        return {'valid': False, 'error': 'URL must be from YouTube (youtube.com, youtu.be, or m.youtube.com)'}
    
    # Check for common YouTube URL issues
    if 'youtube.com' in parsed_url.netloc.lower():
        if '/watch' in parsed_url.path:
            query_params = parse_qs(parsed_url.query)
            if 'v' not in query_params:
                return {'valid': False, 'error': 'YouTube video URL is missing the video ID parameter (v=)'}
            
            video_id = query_params['v'][0]
            if len(video_id) != 11:
                return {'valid': False, 'error': 'Invalid YouTube video ID format'}
        
        elif '/shorts/' in parsed_url.path:
            video_id = parsed_url.path.split('/shorts/')[-1]
            if len(video_id) != 11:
                return {'valid': False, 'error': 'Invalid YouTube Shorts video ID format'}
        
        else:
            return {'valid': False, 'error': 'YouTube URL must be a video (/watch?v=) or shorts (/shorts/) URL'}
    
    return {'valid': False, 'error': 'Invalid YouTube URL format'}

def get_url_type(url):
    """
    Determine the type of YouTube URL
    
    Args:
        url (str): The YouTube URL
    
    Returns:
        str: 'video', 'shorts', or 'unknown'
    """
    
    if '/shorts/' in url:
        return 'shorts'
    elif '/watch' in url:
        return 'video'
    elif 'youtu.be/' in url:
        return 'video'
    else:
        return 'unknown'

def extract_video_id(url):
    """
    Extract video ID from YouTube URL
    
    Args:
        url (str): The YouTube URL
    
    Returns:
        str: The video ID or None if not found
    """
    
    validation_result = validate_youtube_url(url)
    if validation_result['valid']:
        return validation_result['video_id']
    
    return None

def is_youtube_shorts(url):
    """
    Check if the URL is a YouTube Shorts URL
    
    Args:
        url (str): The YouTube URL
    
    Returns:
        bool: True if it's a Shorts URL, False otherwise
    """
    
    return '/shorts/' in url.lower()

def is_youtube_playlist(url):
    """
    Check if the URL is a YouTube playlist URL
    
    Args:
        url (str): The YouTube URL
    
    Returns:
        bool: True if it's a playlist URL, False otherwise
    """
    
    return 'list=' in url.lower()

def normalize_youtube_url(url):
    """
    Normalize YouTube URL to standard format
    
    Args:
        url (str): The YouTube URL
    
    Returns:
        str: Normalized URL or original URL if invalid
    """
    
    video_id = extract_video_id(url)
    if video_id:
        return f"https://www.youtube.com/watch?v={video_id}"
    
    return url
