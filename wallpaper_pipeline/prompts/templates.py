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

Convert the provided image into a short, realistic animated video while preserving the original image exactly:
VIDEO SHOULD NOT HAVE ANY AUDIO OR ANY SOUND.IT SHOULD BE COMPLETELY SILENT.

## Animation Prompt:
{animation_prompt}

Task: Convert the provided image into a short, realistic animated video while preserving the original image exactly.
Remove any text from the image and do not include it in the animation.

PRIORITY:
1. Maintain original identity (face, body, composition, proportions)
2. Maintain original art style, lighting, and colors
3. Apply only subtle, physically realistic motion
4. Do not introduce any new elements

SUBJECT (if human present):
- Keep face perfectly stable and consistent (no distortion or identity drift)
- Natural blinking at relaxed intervals
- Very subtle breathing motion in chest (slow, minimal expansion and contraction)
- Expression remains unchanged or only microscopically softened

HAIR & CLOTHING:
- Hair moves gently with a light, continuous breeze
- Motion is soft and slightly varied across strands
- Loose clothing: minimal edge movement only
- Tight clothing: no movement

ENVIRONMENT (only if visible in image):
- Clouds: slow horizontal drift
- Stars: very soft twinkle or slow rotation
- Water: gentle ripple with low amplitude
- Plants/leaves/flowers: slight natural movement with small variation

GLOBAL MOTION SYSTEM:
- Motion intensity: minimal (micro to subtle only)
- Speed: slow and smooth
- Transitions: eased in and out (no sudden starts/stops)
- Wind: single consistent direction and low intensity
- All elements respond proportionally to the same wind force

VISUAL STABILITY:
- No edge flickering
- No warping or morphing
- No texture crawling
- No frame-to-frame inconsistency

CAMERA:
- Completely static (no zoom, pan, tilt, or shake)

STYLE LOCK:
- Do not restyle or reinterpret the image
- Preserve original textures, shading, and color palette exactly

TIMING:
- Duration: 4–6 seconds
- Seamless loop (end frame matches start frame)

OUTPUT FEEL:
- Calm, natural, cinematic, and realistic

NEGATIVE CONSTRAINTS:
- No added objects or elements
- No exaggerated motion
- No lighting changes
- No camera movement
- No distortion or deformation
- No glitches or artifacts
- No audio"""

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