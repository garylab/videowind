from pathlib import Path

from src.utils.ai_video_generator import AIVideoGenerator

video_gen = AIVideoGenerator()

subtitle_file= "/Users/gary/works/VideoWind/storage/tasks/ef3131e8-fff3-4e66-b44b-fc940adf7247/subtitle.srt"
script = """
Traditional Chinese Medicine (TCM) has been practiced for over 2,000 years, emphasizing balance and harmony in the body. It views health as the flow of Qi, or life energy, through meridians. Acupuncture, a key TCM practice, involves inserting fine needles at specific points to stimulate healing, relieve pain, and restore balance. Herbal medicine, dietary therapy, and mind-body practices like Tai Chi complement acupuncture. TCM focuses on natural healing, treating the root cause rather than just symptoms, promoting overall well-being.
"""

def convert_to_seconds(time_str):
    """ Converts a subtitle time string (hh:mm:ss,SSS) to seconds """
    hours, minutes, rest = time_str.split(":")
    seconds, milliseconds = rest.split(",")
    total_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(milliseconds) / 1000
    return total_seconds

def test_matcher():
    video_paths = [
        "/Users/gary/works/VideoWind/storage/cache_videos/vid-1c2ea1b2507e248610fc570f2e844e29.mp4",
        "/Users/gary/works/VideoWind/storage/cache_videos/vid-3e6e8c4cb2c7c1576a7e50e03e662dea.mp4",
        "/Users/gary/works/VideoWind/storage/cache_videos/vid-5af2c2c5b4eb7c617778f4cfef7b9350.mp4",
        "/Users/gary/works/VideoWind/storage/cache_videos/vid-708def2b38ddb0ae4f8709df51aac2e1.mp4",
        "/Users/gary/works/VideoWind/storage/cache_videos/vid-eb9b94b56c2624ebcd496b1b83bb7179.mp4"
    ]

    subtitle_text = Path(subtitle_file).read_text()
    all_keyframes = {video: video_gen.extract_keyframes(video, interval=2) for video in video_paths if video}
    matched_frames = []

    # Prepare the subtitles and their timing
    subtitle_timing = []
    lines = subtitle_text.split("\n")

    for line in lines:
        if "-->" in line:
            try:
                start_time, end_time = line.split(" --> ")
                start_time = convert_to_seconds(start_time.strip())
                end_time = convert_to_seconds(end_time.strip())
                subtitle_timing.append((start_time, end_time))
            except ValueError:
                # Handle any improperly formatted subtitle lines gracefully
                continue

    # Process the subtitles and match them to keyframes
    subtitle_idx = 0
    for idx, line in enumerate(lines):
        if not line or "-->" in line or line.strip().isdigit():
            continue

        subtitle = line.strip()
        if subtitle_idx >= len(subtitle_timing):
            # If there are more subtitle lines than timings, skip the extra subtitles
            break

        start_time, end_time = subtitle_timing[subtitle_idx]
        subtitle_idx += 1

        for video, frames in all_keyframes.items():
            best_frame, score = video_gen.match_video_with_clip(subtitle, frames)
            if best_frame:
                matched_frames.append((video, best_frame, score, start_time, end_time, subtitle))

    merged_video_path = video_gen.merge_videos_with_subtitles(matched_frames)
    print(f"Final video saved at: {merged_video_path}")
