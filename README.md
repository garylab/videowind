

# Usage
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

To start api server:
```bash
python src/main.py
```

To start Streamlit app:
```bash
streamlit run ./streamlit/Main.py --browser.serverAddress="0.0.0.0" --server.enableCORS=True --browser.gatherUsageStats=False
```

# Backgroun musics
- [www.fesliyanstudios.com](https://www.fesliyanstudios.com/royalty-free-music/downloads-c/short-music/19)
- [www.chosic.com](https://www.chosic.com/free-music/happy/)
- [bensound](https://www.bensound.com/free-music-for-videos)
- [pixabay](https://pixabay.com/music/search/video%20background%20music/)

# Next smarter way
[chatgpt](https://chatgpt.com/share/67d55fd6-6cbc-800d-89c6-0c4005ed9d4a)
```plaintext
Now i have a solution to generate video from script. the steps are:
1. generate audio from script with azure tts, it's duration is AUDIO_DURATION.
2. extract 5 terms from script.
3. get subtitle with whisper large-v3 model.
4. download video clips (without audio) from pexels.com base on terms.
5. generate a video without audio from downloaded clips, the generated video was combined from cropped clips from downloaded video clips. totally the video will be AUDIO_DURATION.
6. Generate final video with subtitle, audio and merged video. 

python
    raw_clips = []
    for video_path in video_paths:
        clip = VideoFileClip(video_path).without_audio()
        clip_duration = clip.duration
        start_time = 0

        while start_time < clip_duration:
            end_time = min(start_time + max_clip_duration, clip_duration)
            split_clip = clip.subclipped(start_time, end_time)
            raw_clips.append(split_clip)
            # logger.info(f"splitting from {start_time:.2f} to {end_time:.2f}, clip duration {clip_duration:.2f}, split_clip duration {split_clip.duration:.2f}")
            start_time = end_time
            if video_concat_mode.value == VideoConcatMode.sequential.value:
                break

Now, i want to make it more smarter.
1. Extract key terms from every sentence of subtitle.
2. Search clips from pexels base on all the terms form subtitle.
3. Set a window WINDOW_SIZE (e.g. 5 seconds) for cropping clips.
4. Get the first term of on sentence, if contains term, crop a clips from downloaded clips, and assign this clips to the duration.
5. next to next window, get the new term, and assign the clip to this duration.
6. If no terms found in this duration, use the preview one to find downloaded clips.
```