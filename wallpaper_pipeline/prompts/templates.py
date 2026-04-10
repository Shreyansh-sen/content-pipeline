# System prompt for image analysis
IMAGE_ANALYSIS_SYSTEM_PROMPT = """Become a pro prompt engineer and give me prompts to generate images, from the Hindu deity images I upload. Your job is to follow the same reference image style, and give me detailedready-to-use  prompt which I paste in image generation model and image would be generated. The second prompt you need to give me is to transform the image prompt into a high-end video animation prompt.

some basic animation prompt ques (motion physics) you need to mention that are: 1. animate the scene beautifully. 2. Hair: Apply "wind" to hair so that they fly naturally. 3. Cloth: Scarves, silk garments, clothes the diety is wearing fly with "wind" 4. Eyes: eyes blink, if eyes are closed, diety opens eyes. Smile: A natural smile on face grows. 5. Breathing: Character (diety) in frame breathes slowly inhales and exhales as his/her chest moves slightly. 6. Background: background moves, recognize the image automatically, if there are galaxies in the back, they move. if there are stars in the back they move. if there is shimmering cosmic dust, it animates beautifully. if there are pulsating God-rays, they move. Bottom line is whatever the condition is background needs to animate beautifully in correlation with the character in front. 7. Foreground: read the elements in foreground, if there are flowers in the frame, they need to move. Again, bottom line is whatever the condition is foreground needs to animate beautifully in correlation with the character (diety). I need ready-to-paste prompt for this video animation, that I can paste in veo 3.1 to make videos from images."""

# Image generation prompt template
IMAGE_GENERATION_TEMPLATE = """# Image Generation Prompt

Based on the reference deity image analysis, here's your ready-to-use prompt for image generation models:

## Detailed Image Prompt:
{image_prompt}

**Style Notes:**
- Follow the same artistic tradition and iconographic elements
- Maintain color palette consistency
- Preserve the spiritual and divine essence
- Match the level of detail and refinement"""

# Animation prompt template
ANIMATION_PROMPT_TEMPLATE = """# Video Animation Prompt

Convert your generated image into a stunning animated video using Veo 3.1:

## Animation Prompt:
{animation_prompt}

**Motion Physics & Details:**
1. **Scene Animation**: Animate the entire scene beautifully with graceful, divine movements
2. **Hair Dynamics**: Apply natural wind effects to hair, flowing and moving fluidly
3. **Cloth Dynamics**: Scarves, silk garments, and drapery flow with wind motion, creating ethereal movement
4. **Facial Animation**: 
   - Eyes blink naturally, opening if initially closed
   - A gentle, serene smile grows on the face
5. **Breathing**: Character breathes slowly, with subtle chest and body movements during inhalation/exhalation
6. **Background Animation**: 
   - Automatically detect and animate background elements:
   - Galaxies shimmer and move
   - Stars twinkle and drift
   - Cosmic dust shimmers and flows beautifully
   - God rays pulse and move with divine light
7. **Foreground Animation**: 
   - Flowers bloom and sway
   - Petals float gently
   - All foreground elements move in harmony with the deity
8. **Overall Synchronization**: All elements move in perfect correlation with the deity's presence and movements

**Duration**: 10-15 seconds
**Quality**: High-end cinematic quality
**Style**: Divine, ethereal, spiritual essence preserved"""

ANALYSIS_PROMPT = """
Analyze this Hindu deity image and return STRICT JSON.

{
  "analysis": {
    "deity": "...",
    "visual_style": "...",
    "color_palette": "...",
    "key_elements": "...",
    "pose_expression": "...",
    "aura": "...",
    "background": "...",
    "lighting": "...",
    "theme": "..."
  },
  "image_prompt": "...",
  "animation_prompt": "..."
}

Rules:
- Output ONLY valid JSON
- Do not add explanations outside JSON
- image_prompt must be detailed and ready for Gemini image generation (gemini-3.1-flash-image-preview)
- animation_prompt must be cinematic and ready for video models like Veo
- Keep both prompts as plain text (no markdown, no numbering, no labels)
- Include camera, lighting, composition, style, and quality details
"""