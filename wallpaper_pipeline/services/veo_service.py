import os
import time
import mimetypes
import subprocess
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
    
    def _remove_audio_from_video(self, video_path: str) -> bool:
        """
        Remove audio from video file using ffmpeg
        Returns True if successful, False otherwise
        """
        try:
            # Create a temporary output file
            temp_output = video_path.replace('.mp4', '_no_audio.mp4')
            
            # Run ffmpeg command to remove audio
            command = [
                'ffmpeg',
                '-i', video_path,
                '-c:v', 'copy',  # Copy video codec without re-encoding
                '-an',  # Remove audio
                '-y',  # Overwrite output file
                temp_output
            ]
            
            result = subprocess.run(command, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                # Replace original with audio-removed version
                os.replace(temp_output, video_path)
                print(f"DEBUG - Audio removed from video: {video_path}")
                return True
            else:
                print(f"DEBUG - ffmpeg failed: {result.stderr}")
                return False
                
        except FileNotFoundError:
            print("DEBUG - ffmpeg not found. Ensure ffmpeg is installed on the system.")
            return False
        except subprocess.TimeoutExpired:
            print("DEBUG - ffmpeg command timed out")
            return False
        except Exception as e:
            print(f"DEBUG - Error removing audio: {e}")
            return False
        
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
            
            # Prepare inputs: Veo takes image parameter if available
            gen_prompt = refined_prompt
            image_input = None
            
            if image_path and os.path.exists(image_path):
                try:
                    import mimetypes
                    # Determine MIME type from file extension
                    mime_type, _ = mimetypes.guess_type(image_path)
                    if not mime_type:
                        mime_type = "image/jpeg"  # Default to JPEG if type cannot be determined
                    
                    with open(image_path, "rb") as image_file:
                        image_data = image_file.read()
                    
                    image_input = types.Image(
                        image_bytes=image_data,
                        mime_type=mime_type
                    )
                    print(f"DEBUG - Image loaded successfully using types.Image: {mime_type}")
                except Exception as e:
                    print(f"DEBUG - Warning: Reference image loading failed: {e}")

            # Start the generation operation
            generate_kwargs = {
                "model": self.model,
                "prompt": gen_prompt,
                "config": types.GenerateVideosConfig(
                    aspect_ratio=self.aspect_ratio,
                    number_of_videos=1,
                    
                ),
            }
            
            # Add image parameter if available
            if image_input:
                generate_kwargs["image"] = image_input
            
            operation = self.client.models.generate_videos(**generate_kwargs)

            print("Waiting for video generation to complete...")
            # Poll the operation until done
            while not operation.done:
                time.sleep(10)
                operation = self.client.operations.get(operation)

            if operation.error:
                raise Exception(f"Video generation failed: {operation.error}")

            if not operation.response and not operation.result:
                raise Exception(f"No response or result in operation: {operation}")

            response = operation.response or operation.result

            # Retrieve the generated video object
            generated_video = response.generated_videos[0]
            
            # Define output paths
            output_filename = f"gen_video_{int(time.time())}.mp4"
            output_path = os.path.join(Config.UPLOAD_FOLDER, output_filename)
            os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
            
            # Download and save the video
            # Note: The SDK download method prepares the file, .save() writes it to disk
            self.client.files.download(file=generated_video.video)
            generated_video.video.save(output_path)
            
            print(f"Generated video saved to {output_path}")
            
            # Remove audio from the generated video
            audio_removed = self._remove_audio_from_video(output_path)
            
            return {
                "success": True,
                "video_url": f"/uploads/{os.path.basename(output_path)}",
                "video_path": output_path,
                "status": "completed",
                "duration": duration,
                "has_audio": False,
                "audio_removed_successfully": audio_removed,
                "message": "Video generated successfully without audio"
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