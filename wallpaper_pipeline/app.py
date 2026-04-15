from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import time
import requests
import threading
from werkzeug.utils import secure_filename
from config.settings import Config
from services.gemini_service import GeminiService
from services.veo_service import VeoService

app = Flask(__name__)
CORS(app)  # Enable CORS for unified pipeline integration

# Configuration
UPLOAD_FOLDER = Config.UPLOAD_FOLDER
ALLOWED_EXTENSIONS = Config.ALLOWED_EXTENSIONS
MAX_FILE_SIZE = Config.MAX_FILE_SIZE

# Thread-safe tracking of processing images
processing_images_lock = threading.Lock()
processing_images = set()

# Create uploads folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Serve uploaded files
@app.route('/uploads/<path:filename>')
def serve_file(filename):
    """Serve uploaded files"""
    return send_from_directory(UPLOAD_FOLDER, filename)

# Initialize Services
gemini_service = GeminiService()
veo_service = VeoService()

# Health check endpoint
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'service': 'wallpaper_pipeline'}), 200


def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Render the upload page"""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    
    # Check if file is in request
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    # Check if file is selected
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Validate file extension
    if not allowed_file(file.filename):
        return jsonify({'error': 'Only JPG/JPEG files are allowed'}), 400
    
    try:
        # Secure the filename
        filename = secure_filename(file.filename)
        
        # Save the file
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        return jsonify({
            'message': 'File uploaded successfully',
            'filename': filename,
            'filepath': filepath
        }), 200
    
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@app.route('/files', methods=['GET'])
def get_files():
    """Get list of uploaded files"""
    try:
        files = os.listdir(app.config['UPLOAD_FOLDER'])
        # Filter only JPG files
        jpg_files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg'))]
        return jsonify({'files': jpg_files}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/analyze', methods=['POST'])
def analyze_image():
    """Analyze uploaded image and generate prompts"""
    
    # Check if file is in request
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    # Check if file is selected
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Validate file extension
    if not allowed_file(file.filename):
        return jsonify({'error': 'Only JPG/JPEG files are allowed'}), 400
    
    try:
        # Save temporary file for analysis
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Analyze image using Gemini to get refined prompts
        analysis_result = gemini_service.analyze_deity_image(filepath)
        
        if not analysis_result['success']:
            return jsonify({'error': analysis_result['error']}), 500
        
        # Prepare response with analysis and prompts only
        response_data = {
            'message': 'Image analyzed and prompts generated successfully',
            'filename': filename,
            'analysis': analysis_result['analysis'],
            'image_prompt': analysis_result['image_prompt'],
            'animation_prompt': analysis_result['animation_prompt']
        }
        
        return jsonify(response_data), 200
    
    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500


@app.route('/generate-video', methods=['POST'])
def generate_video():
    """Generate video from animation prompt and image"""
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        animation_prompt = data.get('animation_prompt')
        image_filename = data.get('filename')
        
        if not animation_prompt:
            return jsonify({'error': 'Animation prompt is required'}), 400
        
        # Build image path if filename provided
        image_path = None
        if image_filename:
            # Try different possible locations
            possible_paths = [
                os.path.join(app.config['UPLOAD_FOLDER'], image_filename),
                os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(image_filename)),
                os.path.join('..', 'unified_pipeline', 'downloads', image_filename),
                os.path.join('..', 'unified_pipeline', 'downloads', os.path.basename(image_filename)),
            ]
            
            for possible_path in possible_paths:
                full_path = os.path.abspath(possible_path)
                if os.path.exists(full_path):
                    image_path = full_path
                    print(f"DEBUG - Found image at: {image_path}")
                    break
            
            if not image_path:
                print(f"DEBUG - Warning: Image file not found for: {image_filename}")
                print(f"DEBUG - Checked paths: {[os.path.abspath(p) for p in possible_paths]}")
        
        print(f"DEBUG - Generating video with prompt: {animation_prompt[:100]}...")
        print(f"DEBUG - Using image: {image_path}")
        
        # Generate video using Veo 3.1
        video_result = veo_service.generate_video_from_prompt(
            prompt=animation_prompt,
            image_path=image_path,
            duration=Config.VIDEO_DURATION
        )
        
        if video_result['success']:
            return jsonify({
                'success': True,
                'message': 'Video generated successfully',
                'video': video_result
            }), 200
        else:
            error_msg = video_result.get('error', 'Unknown error')
            print(f"DEBUG - Video generation returned error: {error_msg}")
            return jsonify({
                'success': False,
                'error': f'Video generation failed: {error_msg}'
            }), 500
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"DEBUG - Video generation error: {error_trace}")
        return jsonify({
            'success': False,
            'error': f'Video generation failed: {str(e)}',
            'traceback': error_trace
        }), 500

# Store for tracking batch generation progress
batch_generation_progress = {}
# Track which image URLs are currently being processed across all batches (thread-safe)
processing_images_lock = threading.Lock()
processing_images = set()

@app.route('/generate-batch-videos', methods=['POST'])
def generate_batch_videos():
    """Generate 2 video variants for each selected image"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        selected_images = data.get('selected_images', [])
        custom_prompt = data.get('custom_prompt', '')
        
        if not selected_images:
            return jsonify({'error': 'No images selected'}), 400
        
        if not custom_prompt:
            return jsonify({'error': 'Custom prompt is required'}), 400
        
        # Filter out images that are already being processed (thread-safe)
        with processing_images_lock:
            images_to_process = [img for img in selected_images if img not in processing_images]
            print(f"DEBUG - Currently processing {len(processing_images)} images")
        
        if not images_to_process:
            return jsonify({
                'error': 'All selected images are already being processed in another batch',
                'message': 'Please select images that are not currently generating'
            }), 400
        
        batch_id = f"batch_{int(time.time())}"
        total_videos = len(images_to_process) * 2
        
        # Initialize progress tracking
        batch_generation_progress[batch_id] = {
            'status': 'starting',
            'total_videos': total_videos,
            'generated_count': 0,
            'images_count': len(images_to_process),
            'selected_images': images_to_process,
            'custom_prompt': custom_prompt,
            'videos': []
        }
        
        print(f"DEBUG - Starting batch generation {batch_id}")
        print(f"DEBUG - Images: {len(images_to_process)}/{len(selected_images)}, Total videos: {total_videos}")
        if len(images_to_process) < len(selected_images):
            print(f"DEBUG - Skipped {len(selected_images) - len(images_to_process)} images already being processed")
        
        # Start background generation
        thread = threading.Thread(
            target=_generate_batch_background,
            args=(batch_id, images_to_process, custom_prompt, veo_service)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'batch_id': batch_id,
            'total_videos': total_videos,
            'message': 'Batch generation started',
            'images_to_process': len(images_to_process),
            'images_skipped': len(selected_images) - len(images_to_process)
        }), 200
        
    except Exception as e:
        import traceback
        print(f"DEBUG - Batch generation error: {traceback.format_exc()}")
        return jsonify({'error': f'Batch generation failed: {str(e)}'}), 500



@app.route('/batch-view')
def batch_view():
    return render_template('batch.html')

@app.route('/batch-progress/<batch_id>', methods=['GET'])
def get_batch_progress(batch_id):
    """Get batch generation progress"""
    try:
        if batch_id not in batch_generation_progress:
            return jsonify({'error': 'Batch not found'}), 404
        
        progress = batch_generation_progress[batch_id]
        return jsonify(progress), 200
        
    except Exception as e:
        return jsonify({'error': f'Error getting progress: {str(e)}'}), 500


def _generate_batch_background(batch_id, selected_images, custom_prompt, veo_service):
    """Background function to generate 2 video variants for each image in parallel"""
    import concurrent.futures
    import time
    import requests
    import os
    from config.settings import Config
    
    try:
        progress = batch_generation_progress[batch_id]
        progress['status'] = 'processing'
        
        def process_image(img_idx, image_url):
            try:
                # Add image to processing set (thread-safe)
                with processing_images_lock:
                    processing_images.add(image_url)
                    print(f"✅ TRACKING: Added {image_url[:50]}... to processing_images (total: {len(processing_images)})")
                
                print(f"🎬 Processing image {img_idx + 1}/{len(selected_images)}")
                
                # Download image
                response = requests.get(
                    image_url,
                    timeout=30,
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                response.raise_for_status()
                
                # Save image
                img_filename = f"batch_img_{batch_id}_{img_idx}_{int(time.time())}.jpg"
                img_path = os.path.join(Config.UPLOAD_FOLDER, img_filename)
                with open(img_path, 'wb') as f:
                    f.write(response.content)
                
                print(f"✅ Downloaded image {img_idx + 1}")
                
                # Generate 2 variants
                for variant in range(1, 3):
                    try:
                        variant_prompt = f"{custom_prompt} (style variation {variant}/2)"
                        print(f"  Generating variant {variant}/2 for image {img_idx+1}...")
                        
                        # Generate video
                        video_result = veo_service.generate_video_from_prompt(
                            prompt=variant_prompt,
                            image_path=img_path,
                            duration=Config.VIDEO_DURATION
                        )
                        
                        if video_result.get('success'):
                            progress['videos'].append({
                                'image_index': img_idx,
                                'variant': variant,
                                'prompt': variant_prompt,
                                'video_url': video_result.get('video_url'),
                                'video_path': video_result.get('video_path')
                            })
                            print(f"    ✅ Variant {variant} for image {img_idx+1} generated")
                        else:
                            print(f"    ❌ Variant {variant} for image {img_idx+1} failed: {video_result.get('error')}")
                            
                    except Exception as e:
                        print(f"    ❌ Error generating variant {variant} for image {img_idx+1}: {e}")
                    
                    progress['generated_count'] += 1
                
                # Clean up image
                try:
                    os.remove(img_path)
                except:
                    pass
            except Exception as e:
                print(f"❌ Failed to process image {img_idx + 1}: {e}")
            finally:
                # Remove image from processing set when done (thread-safe)
                with processing_images_lock:
                    processing_images.discard(image_url)
                    print(f"✅ TRACKING: Removed {image_url[:50]}... from processing_images (total: {len(processing_images)})")

        # Use ThreadPoolExecutor to run image processing in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(selected_images)) as executor:
            futures = [executor.submit(process_image, i, url) for i, url in enumerate(selected_images)]
            concurrent.futures.wait(futures)
            
        progress['status'] = 'completed'
        print(f"✅ Batch {batch_id} completed: {progress['generated_count']} videos generated")
        
    except Exception as e:
        import traceback
        print(f"❌ Background generation error: {traceback.format_exc()}")
        progress = batch_generation_progress.get(batch_id)
        if progress:
            progress['status'] = 'error'
            progress['error'] = str(e)


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors by returning JSON"""
    return jsonify({'error': 'Endpoint not found', 'path': request.path}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors by returning JSON"""
    return jsonify({'error': 'Internal server error', 'message': str(error)}), 500

if __name__ == '__main__':
    app.run(debug=Config.DEBUG, host=Config.HOST, port=Config.PORT)