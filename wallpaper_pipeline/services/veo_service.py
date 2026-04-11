import os
import time
from typing import Dict, Optional
from config.settings import Config
from google import genai
from google.genai import types

class VeoService:
    """Service to handle Google Veo 3.1 video generation API calls"""
    def __init__(self):
        self.client = genai.Client(
            api_key=Config.GEMINI_API_KEY,
        )
        self.model = Config.VIDEO_MODEL
        self.video_duration = Config.VIDEO_DURATION
        self.aspect_ratio = Config.VIDEO_ASPECT_RATIO
        
    def generate_video_from_prompt(
        self, 
        prompt: str,
        image_path: Optional[str] = None,
        duration: int = 10
    ) -> Dict:
        """
        Generate video using Gemini Veo 3.1 with animation prompt and optional reference image
        """
        try:
            print(f"DEBUG - Generating video with {self.model} using google-genai SDK")
            
            # Format the visual description
            refined_prompt = (
                f"{prompt}. High quality cinematic rendering, smooth animations, "
                f"divine ethereal quality. Video duration: {duration} seconds."
            )
            
            # Prepare inputs: Veo takes a list if there is an image, or a string if just text
            gen_prompt = refined_prompt
            if image_path and os.path.exists(image_path):
                try:
                    uploaded_file = self.client.files.upload(path=image_path)
                    gen_prompt = [uploaded_file, refined_prompt]
                    print(f"DEBUG - Uploaded reference image: {uploaded_file.name}")
                except Exception as e:
                    print(f"DEBUG - Warning: Reference image upload failed: {e}")

            # Start the generation operation
            operation = self.client.models.generate_videos(
                model=self.model,
                prompt=gen_prompt,
                config=types.GenerateVideosConfig(
                    aspect_ratio=self.aspect_ratio,
                ),
            )

            print("Waiting for video generation to complete...")
            # Poll the operation until done
            while not operation.done:
                time.sleep(10)
                operation = self.client.operations.get(operation)

            # Retrieve the generated video object
            generated_video = operation.response.generated_videos[0]
            
            # Define output paths
            output_filename = f"gen_video_{int(time.time())}.mp4"
            output_path = os.path.join(Config.GENERATED_VIDEO_FOLDER, output_filename)
            os.makedirs(Config.GENERATED_VIDEO_FOLDER, exist_ok=True)
            
            # Download and save the video
            # Note: The SDK download method prepares the file, .save() writes it to disk
            self.client.files.download(file=generated_video.video)
            generated_video.video.save(output_path)
            
            print(f"Generated video saved to {output_path}")
            
            return {
                "success": True,
                "video_url": f"/generated-videos/{output_filename}",
                "video_path": output_path,
                "status": "completed",
                "duration": duration,
                "has_audio": False,
                "message": "Video generated successfully"
            }
                
        except Exception as e:
            import traceback
            print(f"Error during Veo Generation: {traceback.format_exc()}")
            return {
                "success": False,
                "error": f"Error generating video: {str(e)}",
                "traceback": traceback.format_exc()
            }
            
    def generate_video_with_hume(
        self,
        prompt: str,
        image_path: Optional[str] = None,
        duration: int = 10
    ) -> Dict:
        return {"success": False, "error": "Hume fallback disabled"}