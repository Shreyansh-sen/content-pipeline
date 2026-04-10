import base64
import json
import requests
from typing import Dict, Tuple
from config.settings import Config
from prompts.templates import IMAGE_ANALYSIS_SYSTEM_PROMPT, ANALYSIS_PROMPT

class GeminiService:
    def __init__(self):
        self.api_key = Config.GEMINI_API_KEY
        self.base_url = Config.GEMINI_BASE_URL
        self.prompt_model = Config.PROMPT_MODEL
        self.advanced_model = Config.ADVANCED_MODEL
        self.image_model = Config.IMAGE_MODEL

    def _headers(self) -> Dict[str, str]:
        return {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
        }

    def _model_url(self, model_name: str) -> str:
        return f"{self.base_url}/{model_name}:generateContent"
        
    def encode_image_to_base64(self, image_path: str) -> str:
        """Convert image file to base64 string"""
        with open(image_path, 'rb') as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def analyze_deity_image(self, image_path: str) -> Dict:
        """
        Analyze a deity image using Gemini's vision capabilities
        Returns analysis data and generated prompts
        """
        try:
            # Encode image to base64
            image_data = self.encode_image_to_base64(image_path)
            
            url = self._model_url(self.advanced_model)

            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {
                                "text": f"{IMAGE_ANALYSIS_SYSTEM_PROMPT}\n\n{ANALYSIS_PROMPT}\n\nIMPORTANT: Respond ONLY with valid JSON (no markdown, no code blocks) with these exact keys: 'analysis', 'image_prompt', and 'animation_prompt'. Do not wrap in ```json or any code blocks."
                            },
                            {
                                "inline_data": {
                                    "mime_type": "image/jpeg",
                                    "data": image_data
                                }
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.7,
                    "max_output_tokens": 15000
                }
            }
            
            print(f"DEBUG - Making Gemini API request to: {url}")
            response = requests.post(url, headers=self._headers(), json=payload)
            
            print(f"DEBUG - API Status Code: {response.status_code}")
            print(f"DEBUG - API Response Text: {response.text[:500]}")
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"API Error: {response.status_code} - {response.text}"
                }
                
            result = response.json()
            
            try:
                # Parse Gemini response
                analysis_text = result['candidates'][0]['content']['parts'][0]['text'].strip()
                print(f"DEBUG - Analysis Response: {analysis_text[:500]}")
                
                # Extract prompts from the response
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
                
            except (KeyError, IndexError) as e:
                return {"success": False, "error": f"Failed to parse Gemini response: {str(e)}"}
                
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
            # Strip markdown code block wrapper if present
            cleaned_text = analysis_text.strip()
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text[7:]  # Remove ```json
            if cleaned_text.startswith('```'):
                cleaned_text = cleaned_text[3:]  # Remove ```
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text[:-3]  # Remove trailing ```
            cleaned_text = cleaned_text.strip()
            
            # Parse JSON
            analysis_data = json.loads(cleaned_text)
            
            # Handle nested structure where prompts might be at root or under 'analysis' key
            image_prompt = analysis_data.get('image_prompt', '')
            animation_prompt = analysis_data.get('animation_prompt', '')
            
            # If not found at root, check if they're nested
            if not image_prompt or not animation_prompt:
                analysis_obj = analysis_data.get('analysis', {})
                if isinstance(analysis_obj, dict):
                    image_prompt = image_prompt or analysis_obj.get('image_prompt', '')
                    animation_prompt = animation_prompt or analysis_obj.get('animation_prompt', '')
            
            print(f"DEBUG - Extracted prompts - Image: {image_prompt[:100]}, Animation: {animation_prompt[:100]}")
            return image_prompt, animation_prompt
        except json.JSONDecodeError as e:
            print(f"DEBUG - Failed to parse JSON: {e}")
            print(f"DEBUG - Response text: {analysis_text[:1000]}")
            # Return empty strings, caller should handle gracefully
            return "", ""
    
    def generate_image_prompt(self, analysis_text: str) -> str:
        """Generate a detailed image generation prompt from analysis using Gemini"""
        try:
            url = self._model_url(self.prompt_model)
            
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {
                                "text": f"""Based on this image analysis:
                                
{analysis_text}

Generate a detailed, professional image generation prompt that can be pasted directly into image generation models 
(like DALL-E, Midjourney, etc). The prompt should capture all the style, characteristics, and divine essence."""
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.8,
                    "max_output_tokens": 10000
                }
            }
            
            response = requests.post(url, headers=self._headers(), json=payload)
            
            if response.status_code == 200:
                return response.json()['candidates'][0]['content']['parts'][0]['text']
            else:
                return f"Error generating prompt: {response.status_code}"
                
        except Exception as e:
            return f"Error: {str(e)}"
    
    def generate_animation_prompt(self, analysis_text: str, image_prompt: str) -> str:
        """Generate a detailed animation prompt for video generation using Gemini"""
        try:
            url = self._model_url(self.prompt_model)
            
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {
                                "text": f"""Based on this deity image analysis:

{analysis_text}

And this image generation prompt:

{image_prompt}

Generate a comprehensive animation prompt for video generation that includes:
1. Hair flowing with natural wind physics
2. Cloth and scarves fluttering gracefully
3. Eyes blinking and expressions showing serenity
4. Breathing with chest movements
5. Background elements (galaxies, stars, cosmic dust, god rays) animating beautifully
6. Foreground elements (flowers, petals) moving gracefully
7. Overall divine, ethereal quality maintained

The prompt should be ready to paste directly into video generation models like Veo 3.1."""
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.8,
                    "max_output_tokens": 15000
                }
            }
            
            response = requests.post(url, headers=self._headers(), json=payload)
            
            if response.status_code == 200:
                return response.json()['candidates'][0]['content']['parts'][0]['text']
            else:
                return f"Error generating animation prompt: {response.status_code}"
                
        except Exception as e:
            return f"Error: {str(e)}"

    def generate_image_from_prompt(self, prompt: str) -> Dict:
        """Generate an image via Gemini image preview model from a text prompt."""
        try:
            url = self._model_url(self.image_model)
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ]
            }

            response = requests.post(url, headers=self._headers(), json=payload)
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"API Error: {response.status_code} - {response.text}"
                }

            result = response.json()
            parts = result.get('candidates', [{}])[0].get('content', {}).get('parts', [])

            image_base64 = ""
            text_response = ""
            for part in parts:
                inline_data = part.get('inlineData') or part.get('inline_data')
                if inline_data and inline_data.get('data'):
                    image_base64 = inline_data.get('data')
                if part.get('text'):
                    text_response = part.get('text')

            return {
                "success": True,
                "image_base64": image_base64,
                "text": text_response,
                "raw": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error generating image: {str(e)}"
            }
