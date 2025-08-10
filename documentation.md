# YT Playlist Sorter & Tracker - User Guide

Welcome to YT Playlist Sorter & Tracker! This guide will help you get started and make the most of all features in the app.

## Table of Contents
1. Getting Started
2. Google API Key Setup
3. Sorting a YouTube Playlist
4. Viewing Channel Playlists
5. Tracking Viewed Playlists
6. Configuration Tab
7. Tips & Troubleshooting

---

## 1. Getting Started
- Launch the app from your Start Menu or Desktop shortcut.
- The main window has four tabs: Sort Playlist, Channel Playlists, Viewed Playlists, and Configurations.

## 2. Google API Key Setup
**Required for all features.**
- Go to the **Configurations** tab.
- Follow the instructions to obtain a Google API Key for YouTube Data API v3.
- Paste your API key in the input box and click **Save API Key**.
- If the key is valid, you can use all features of the app.

## 3. Sorting a YouTube Playlist
- Go to the **Sort Playlist** tab.
- Enter the full YouTube Playlist URL in the input box.
- Choose your sorting preference:
  - Sort by Added Time (Ascending/Descending)
  - Sort by Published Time (Ascending/Descending)
- Click **Sort Playlist**.
- The app will fetch and display all videos in the playlist, sorted as selected.
- Each video card shows:
  - Thumbnail
  - Title
  - Date added
  - Direct link to the video
- Click a video link to mark it as viewed (link color changes).
- New videos since last retrieval are highlighted at the top.

## 4. Viewing Channel Playlists
- Go to the **Channel Playlists** tab.
- Enter a YouTube Channel URL (either `/channel/CHANNEL_ID` or `/@handle`).
- Click **List Channel Playlists**.
- All playlists from the channel will be listed.
- Each entry shows:
  - Playlist title
  - Playlist link
  - **Load to sorter** button to quickly sort that playlist in the Sort Playlist tab.

## 5. Tracking Viewed Playlists
- Go to the **Viewed Playlists** tab.
- All playlists you have previously loaded are shown as cards.
- Each card displays:
  - Number of videos
  - Channel name
  - Playlist name
  - New videos count (after checking)
  - **Check** button to update new videos count
  - **Load to sorter** button to reload the playlist in the Sort Playlist tab
- Use **check all** to update new videos count for all playlists at once.

## 6. Configuration Tab
- Centered card layout for API key management.
- Step-by-step instructions for obtaining a Google API Key.
- Status messages for API key validity and errors.

## 7. Tips & Troubleshooting
- If you see API errors, check your API key and quota in the Google Cloud Console.
- Make sure your API key has access to YouTube Data API v3.
- If the app does not show new videos, click **Check** or **Check All** in the Viewed Playlists tab.
- To refresh viewed playlists, switch to the Viewed Playlists tab.
- If you change your API key, update it in the Configurations tab.
- For best results, use valid YouTube URLs and ensure your internet connection is active.

---

**Enjoy using YT Playlist Sorter & Tracker!**

For further help, contact the developer or refer to the Configurations tab for API setup instructions.
