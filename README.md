# YouTube Playlist Sorter and Tracker

A desktop application to sort YouTube playlist videos by the date they were added, and display clickable video links. Built with Python and PyQt5.

## Features
- Enter a YouTube playlist URL
- Sort videos in ascending or descending order by date added
- Clickable video links open in your default browser

## Requirements
- Python 3.7+
- PyQt5
- requests
- python-dotenv
- YouTube Data API v3 enabled and API key in `.env`
- 
## Setup 1
1. donwload the YTPlaylistSorterSetup.exe.
2. Run the .exe and install the app.
3. Create a Google API key with YouTube Data API v3 enabled:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/).
   - Create a new project (or select an existing one).
   - In the left sidebar, go to **APIs & Services > Library**.
   - Search for "YouTube Data API v3" and click **Enable**.
   - Go to **APIs & Services > Credentials**.
   - Click **Create Credentials** > **API key**.
   - Copy your API key.
   - paste it in the configurations tab of the app.

## Setup 2
1. Clone or download this repository.
2. Install dependencies:
   ```bash
   pip install PyQt5 requests python-dotenv
   ```
3. Create a Google API key with YouTube Data API v3 enabled:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/).
   - Create a new project (or select an existing one).
   - In the left sidebar, go to **APIs & Services > Library**.
   - Search for "YouTube Data API v3" and click **Enable**.
   - Go to **APIs & Services > Credentials**.
   - Click **Create Credentials** > **API key**.
   - Copy your API key.
   - Create a `.env` file in the project directory and add:
     ```env
     GOOGLE_API_KEY=YOUR_API_KEY_HERE
     ```
4. Run the application:
   ```bash
   python main_app.py
   ```

## Usage
1. Enter a YouTube playlist URL in the input field.
2. Select sorting order (Ascending/Descending).
3. Click "Sort Playlist".
4. Click any video link to open it in your default browser.

## Notes
- The app uses the YouTube Data API v3 to fetch playlist items.
- Only public playlists are supported.
- If you see API errors, check your API key and quota.

## License
MIT
