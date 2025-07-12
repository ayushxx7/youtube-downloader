# YouTube Downloader

A simple Streamlit web app to download YouTube videos and audio in various formats and qualities using yt-dlp and ffmpeg.

## Features
- Download YouTube videos and shorts
- Choose video quality and audio format
- Real-time download progress
- Download as video+audio or audio-only

## Requirements
- Python 3.11+
- [ffmpeg](https://ffmpeg.org/) (must be installed on your system)

## Setup

1. **Clone the repository:**
   ```sh
   git clone <your-repo-url>
   cd YouTubeDownloader-2
   ```
2. **Install Python dependencies:**
   ```sh
   pip install -r requirements.txt
   # or, if using uv/pyproject.toml:
   uv pip install -r requirements.txt
   ```
   Or use the provided `pyproject.toml` with your preferred tool (e.g., `uv`, `pip`, or `poetry`).

3. **Install ffmpeg:**
   - **macOS:** `brew install ffmpeg`
   - **Ubuntu:** `sudo apt-get install ffmpeg`
   - **Windows:** [Download from ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH

4. **Run the app:**
   ```sh
   streamlit run app.py
   ```

## Using [uv](https://github.com/astral-sh/uv) (Recommended for Fast Python Projects)

1. **Initialize the project (if not already initialized):**
   ```sh
   uv init
   ```
   *(Skip this if `pyproject.toml` already exists)*

2. **Install dependencies:**
   ```sh
   uv sync
   ```
   or, if you want to use requirements.txt:
   ```sh
   uv pip install -r requirements.txt
   ```

3. **Run the app:**
   ```sh
   uv run streamlit run app.py
   ```

## Usage
- Enter a YouTube video or shorts URL.
- Click "Get Video Info" to preview details.
- Select download options and click "Start Download".
- When complete, click the download button to save the file.

## Project Structure
- `app.py` — Main Streamlit app
- `utils/` — Helper modules for downloading, file management, and validation
- `pyproject.toml` — Project dependencies
- `.gitignore` — Files and folders to exclude from Git

## Tests
- install requirements from `requirements-dev.txt` and run
```sh
   pytest -n auto
```

## Contributing
Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License
Specify your license here (e.g., MIT, Apache 2.0, etc.) 