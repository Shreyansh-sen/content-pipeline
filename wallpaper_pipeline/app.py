from flask import Flask, render_template, request, jsonify, send_from_directory
import os
from werkzeug.utils import secure_filename
from config.settings import Config
from services.gemini_service import GeminiService
from services.veo_service import VeoService
from services.orchestrator_service import WallpaperOrchestratorService

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = Config.UPLOAD_FOLDER
ALLOWED_EXTENSIONS = Config.ALLOWED_EXTENSIONS
MAX_FILE_SIZE = Config.MAX_FILE_SIZE

# Create uploads folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

os.makedirs(Config.SHARED_OUTPUT_FOLDER, exist_ok=True)
os.makedirs(Config.GENERATED_VIDEO_FOLDER, exist_ok=True)
os.makedirs(Config.BATCH_SOURCE_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Initialize Services
gemini_service = GeminiService()
veo_service = VeoService()     
orchestrator_service = WallpaperOrchestratorService(gemini_service, veo_service)


def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Render the upload page"""
    return render_template('index.html')


@app.route('/generated-videos/<path:filename>')
def generated_videos(filename):
    """Serve generated videos from the shared output directory"""
    return send_from_directory(Config.GENERATED_VIDEO_FOLDER, filename)


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
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
            if not os.path.exists(image_path):
                print(f"DEBUG - Warning: Image file not found at {image_path}")
                image_path = None
        
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
                'message': 'Video generated successfully',
                'video': video_result
            }), 200
        else:
            error_msg = video_result.get('error', 'Unknown error')
            return jsonify({'error': f'Video generation failed: {error_msg}'}), 500
    
    except Exception as e:
        import traceback
        print(f"DEBUG - Video generation error: {traceback.format_exc()}")
        return jsonify({'error': f'Video generation failed: {str(e)}'}), 500


@app.route('/api/batch-generate', methods=['POST'])
def batch_generate_videos():
    """Generate videos for multiple Pinterest image URLs"""
    try:
        data = request.get_json(silent=True) or {}
        image_urls = data.get('image_urls') or data.get('imageUrls') or []
        duration = data.get('duration', Config.VIDEO_DURATION)

        if not isinstance(image_urls, list) or not image_urls:
            return jsonify({'error': 'image_urls must be a non-empty list'}), 400

        batch_result = orchestrator_service.process_image_urls(image_urls=image_urls, duration=duration)
        return jsonify(batch_result), 200
    except Exception as e:
        import traceback
        print(f"DEBUG - Batch generation error: {traceback.format_exc()}")
        return jsonify({'error': f'Batch generation failed: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=Config.DEBUG, host=Config.HOST, port=Config.PORT)
