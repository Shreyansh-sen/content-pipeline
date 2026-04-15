import base64
import json
from typing import Dict, Tuple
import requests
from config.settings import Config
from prompts.templates import (
    IMAGE_ANALYSIS_SYSTEM_PROMPT,
    ANALYSIS_PROMPT,
)


class OpenAIService:
    """Service to handle Azure OpenAI API calls for image analysis and prompt generation"""
    
    def __init__(self):
        self.azure_endpoint = Config.AZURE_ENDPOINT
        self.api_key = Config.API_KEY
        self.api_version = Config.API_VERSION
        self.deployment_name = Config.DEPLOYMENT_NAME
    
    def encode_image_to_base64(self, image_path: str) -> str:
        """Convert image file to base64 string"""
        with open(image_path, 'rb') as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def analyze_deity_image(self, image_path: str) -> Dict:
        """
        Analyze a Hindu deity image using GPT-4O mini vision capabilities
        Returns analysis data and generated prompts
        """
        try:
            # Encode image to base64
            image_data = self.encode_image_to_base64(image_path)
            
            # Prepare the API request
            headers = {
                "Content-Type": "application/json",
                "api-key": self.api_key
            }
            
            # Build the correct API URL
            url = f"{self.azure_endpoint}openai/deployments/{self.deployment_name}/chat/completions?api-version={self.api_version}"
            
            payload = {
                "messages": [
                    {
                        "role": "system",
                        "content": IMAGE_ANALYSIS_SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            },
                            {
                                "type": "text",
                                "text": ANALYSIS_PROMPT
                            }
                        ]
                    }
                ],
                "max_completion_tokens": 15000
            }
            
            # Make API request
            print(f"DEBUG - Making API request to: {url}")
            print(f"DEBUG - Headers: {headers}")
            print(f"DEBUG - Payload keys: {payload.keys()}")
            
            response = requests.post(url, headers=headers, json=payload)
            
            print(f"DEBUG - API Status Code: {response.status_code}")
            print(f"DEBUG - API Response Text: {response.text}")
            print(f"DEBUG - API Response Length: {len(response.text)}")
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"API Error: {response.status_code} - {response.text}"
                }
            
            # Parse response
            result = response.json()
            analysis_text = result['choices'][0]['message']['content']
            
            print(f"DEBUG - API Response: {analysis_text[:500]}")
            
            # Extract image and animation prompts from analysis
            image_prompt, animation_prompt = self._extract_prompts(analysis_text)
            if not image_prompt or not animation_prompt:
                return {
                    "success": False,
                    "error": "Failed to extract prompts from analysis"
                }
            
            return {
                "success": True,
                "analysis": analysis_text,
                "image_prompt": image_prompt,
                "animation_prompt": animation_prompt
            }
            
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"JSON parsing error: {str(e)}"
            }
        except Exception as e:
            import traceback
            return {
                "success": False,
                "error": f"Error analyzing image: {str(e)}\n{traceback.format_exc()}"
            }
    
    def _extract_prompts(self, analysis_text: str) -> Tuple[str, str]:
        """Extract image and animation prompts from analysis text"""
        try:
            # Parse the JSON response from the LLM
            analysis_data = json.loads(analysis_text)
            
            # Extract the prompts directly from the LLM response
            image_prompt = analysis_data.get('image_prompt', '')
            animation_prompt = analysis_data.get('animation_prompt', '')
            
            return image_prompt, animation_prompt
        except json.JSONDecodeError as e:
            print(f"DEBUG - Failed to parse JSON: {e}")
            print(f"DEBUG - Response text: {analysis_text[:1000]}")
            raise
    
    def generate_image_prompt(self, analysis_text: str) -> str:
        """Generate a detailed image generation prompt from analysis"""
        try:
            headers = {
                "Content-Type": "application/json",
                "api-key": self.api_key
            }
            
            url = f"{self.azure_endpoint}openai/deployments/{self.deployment_name}/chat/completions?api-version={self.api_version}"
            
            payload = {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert prompt engineer. Generate detailed, professional image generation prompts."
                    },
                    {
                        "role": "user",
                        "content": f"""Based on this image analysis:
                        
{analysis_text}

Generate a detailed, ready-to-use image generation prompt that can be pasted directly into image generation models 
(like DALL-E, Midjourney, etc). The prompt should capture all the style, characteristics, and divine essence."""
                    }
                ],
                "max_completion_tokens": 10000
            }
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                return f"Error generating prompt: {response.status_code}"
                
        except Exception as e:
            return f"Error: {str(e)}"
    
    def generate_animation_prompt(self, analysis_text: str, image_prompt: str) -> str:
        """Generate a detailed animation prompt for video generation"""
        try:
            headers = {
                "Content-Type": "application/json",
                "api-key": self.api_key
            }
            
            url = f"{self.azure_endpoint}openai/deployments/{self.deployment_name}/chat/completions?api-version={self.api_version}"
            
            payload = {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert in creating animation prompts for video generation models like Veo 3.1."
                    },
                    {
                        "role": "user",
                        "content": f"""Based on this Hindu deity image analysis:

{analysis_text}

And this image generation prompt:

{image_prompt}

Generate a comprehensive animation prompt for Veo 3.1 that includes:
1. Hair flowing with natural wind physics
2. Cloth and scarves fluttering gracefully
3. Eyes blinking and expressions showing serenity
4. Breathing with chest movements
5. Background elements (galaxies, stars, cosmic dust, god rays) animating beautifully
6. Foreground elements (flowers, petals) moving gracefully
7. Overall divine, ethereal quality maintained

The prompt should be ready to paste directly into Veo 3.1 for video generation."""
                    }
                ],
                "max_completion_tokens": 15000
            }
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                return f"Error generating animation prompt: {response.status_code}"
                
        except Exception as e:
            return f"Error: {str(e)}"