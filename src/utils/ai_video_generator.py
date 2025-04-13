import open_clip
import torch
import os
from moviepy import VideoFileClip, concatenate_videoclips, TextClip
from PIL import Image


class AIVideoGenerator:
    def __init__(self):
        model_name = "ViT-B-32"  # You can change the model based on your needs
        self.model, _, self.clip_preprocess = open_clip.create_model_and_transforms(model_name, pretrained="laion2b_s34b_b79k")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        self.model.eval()  # Set the model to evaluation mode
        self.tokenizer = open_clip.get_tokenizer(model_name)

    def extract_keyframes(self, video_path, output_dir="keyframes", interval=1):
        """ Extract keyframes from a video at a set interval (in seconds) """
        os.makedirs(output_dir, exist_ok=True)
        video = VideoFileClip(video_path)
        keyframes = []

        for t in range(0, int(video.duration), interval):
            frame_path = os.path.join(output_dir, f"{os.path.basename(video_path)}_{t}.jpg")
            frame = video.get_frame(t)
            Image.fromarray(frame).save(frame_path)
            keyframes.append(frame_path)

        return keyframes

    def match_video_with_clip(self, text, frame_paths):
        """ Use CLIP to find the best matching frame for a given subtitle text """
        # Tokenize and encode the text
        text_input = self.tokenizer([text]).to(self.device)
        text_features = self.model.encode_text(text_input)
        text_features /= text_features.norm(dim=-1, keepdim=True)

        best_frame, best_score = None, -1

        for frame_path in frame_paths:
            # Preprocess image and encode it
            image = self.clip_preprocess(Image.open(frame_path)).unsqueeze(0).to(self.device)
            image_features = self.model.encode_image(image)
            image_features /= image_features.norm(dim=-1, keepdim=True)

            # Compute cosine similarity
            similarity = torch.cosine_similarity(text_features, image_features).item()
            if similarity > best_score:
                best_score, best_frame = similarity, frame_path

        return best_frame, best_score

    def merge_videos_with_subtitles(self, matched_frames, output_filename="final_video.mp4"):
        """ Merge video clips into one final video with subtitles """
        clips = []
        for video_path, best_frame, score, start_time, end_time, subtitle in matched_frames:
            if start_time >= video_clip.duration:
                break
            video_clip = VideoFileClip(video_path).subclipped(start_time, end_time)
            text_clip = TextClip(text=subtitle, font="/Users/gary/works/VideoWind/tests/files/fonts/JosefinSans-Light.ttf", font_size=24, color='white', bg_color='black', size=video_clip.size)
            text_clip = text_clip.with_position('bottom').with_duration(video_clip.duration)
            final_clip = concatenate_videoclips([video_clip, text_clip.with_start(0)])
            clips.append(final_clip)

        final_video = concatenate_videoclips(clips, method="compose")
        final_video.write_videofile(output_filename, codec="libx264", fps=24)
        return output_filename
