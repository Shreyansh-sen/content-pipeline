import requests
import json
from typing import Dict, Optional
from config.settings import Config


class HumeAIService:
    """Service to handle Hume AI API calls for video and live image generation"""
    
    def __init__(self):
        self.api_key = Config.HUME_APIKEY
        self.api_secret = Config.HUME_APISECRET
        self.api_endpoint = Config.HUME_API_ENDPOINT
        self.video_duration = Config.VIDEO_DURATION
        
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for Hume AI API"""
        return {
            "X-Hume-API-Key": self.api_key,
            "X-Hume-API-Secret": self.api_secret,
            "Content-Type": "application/json"
        }
    
    def generate_video_from_prompt(
        self, 
        prompt: str,
        reference_image_path: Optional[str] = None,
        output_format: str = "mp4"
    ) -> Dict:
        """
        Generate video using Hume AI with refined prompt and reference image
        10 seconds, no sound
        
        Args:
            prompt: The refined animation prompt
            reference_image_path: Path to the reference deity image
            output_format: Output video format (default: mp4)
            
        Returns:
            Dictionary with video generation result
        """
        try:
            headers = self.get_auth_headers()
            
            # Prepare request payload
            payload = {
                "prompt": prompt,
                "duration": self.video_duration,
                "format": output_format,
                "include_audio": False,  # No sound as per requirement
                "quality": "high",
                "style": "cinematic"
            }
            
            # Add reference image if provided
            if reference_image_path:
                with open(reference_image_path, 'rb') as img_file:
                    image_data = img_file.read()
                
                # Use multipart form data for image upload
                files = {
                    'image': ('reference_image.jpg', image_data, 'image/jpeg'),
                    'payload': (None, json.dumps(payload), 'application/json')
                }
                
                url = f"{self.api_endpoint}/video/generate"
                response = requests.post(url, headers=headers, files=files)
            else:
                # Text-only generation
                url = f"{self.api_endpoint}/video/generate"
                response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code in [200, 201]:
                result = response.json()
                return {
                    "success": True,
                    "video_id": result.get('id'),
                    "video_url": result.get('output_url'),
                    "status": result.get('status'),
                    "duration": self.video_duration,
                    "has_audio": False
                }
            else:
                return {
                    "success": False,
                    "error": f"Video generation failed: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error generating video: {str(e)}"
            }
    
    def generate_live_image_from_prompt(
        self,
        prompt: str,
        reference_image_path: Optional[str] = None,
        style: str = "photorealistic"
    ) -> Dict:
        """
        Generate live/animated still image using Hume AI
        
        Args:
            prompt: The refined image generation prompt
            reference_image_path: Path to the reference deity image
            style: Image generation style
            
        Returns:
            Dictionary with image generation result
        """
        try:
            headers = self.get_auth_headers()
            
            # Prepare request payload
            payload = {
                "prompt": prompt,
                "format": "png",
                "quality": "high",
                "style": style,
                "include_reference": True if reference_image_path else False
            }
            
            # Add reference image if provided
            if reference_image_path:
                with open(reference_image_path, 'rb') as img_file:
                    image_data = img_file.read()
                
                # Use multipart form data for image upload
                files = {
                    'image': ('reference_image.jpg', image_data, 'image/jpeg'),
                    'payload': (None, json.dumps(payload), 'application/json')
                }
                
                url = f"{self.api_endpoint}/image/generate"
                response = requests.post(url, headers=headers, files=files)
            else:
                # Text-only generation
                url = f"{self.api_endpoint}/image/generate"
                response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code in [200, 201]:
                result = response.json()
                return {
                    "success": True,
                    "image_id": result.get('id'),
                    "image_url": result.get('output_url'),
                    "image_data": result.get('image_base64'),
                    "status": result.get('status')
                }
            else:
                return {
                    "success": False,
                    "error": f"Image generation failed: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error generating image: {str(e)}"
            }
    
    def check_generation_status(self, generation_id: str, generation_type: str = "video") -> Dict:
        """
        Check the status of a video or image generation request
        
        Args:
            generation_id: The ID of the generation request
            generation_type: Type of generation ('video' or 'image')
            
        Returns:
            Dictionary with current generation status
        """
        try:
            headers = self.get_auth_headers()
            url = f"{self.api_endpoint}/{generation_type}/status/{generation_id}"
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "status": result.get('status'),
                    "progress": result.get('progress'),
                    "output_url": result.get('output_url'),
                    "id": generation_id
                }
            else:
                return {
                    "success": False,
                    "error": f"Status check failed: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error checking status: {str(e)}"
            }
