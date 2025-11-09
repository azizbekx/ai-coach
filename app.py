"""
AI Gymnastics Coach - Web Application
FastAPI backend for video upload and live webcam analysis
"""

import os
import json
import base64
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional
import uvicorn

from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import cv2
import numpy as np
from typing import Optional

from video_processor import VideoProcessor

# Gemini Vision API (optional)
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: google-genai not installed. Gemini Vision API will not be available.")

# Initialize FastAPI app
app = FastAPI(
    title="AI Gymnastics Coach",
    description="Olympic-Level Training System with Computer Vision",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
UPLOAD_FOLDER = Path('uploads')
OUTPUT_FOLDER = Path('outputs')
UPLOAD_FOLDER.mkdir(exist_ok=True)
OUTPUT_FOLDER.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize video processor (it creates its own pose estimator, analyzer, and feedback generator)
video_processor = VideoProcessor()

# Initialize Gemini client (optional)
gemini_client = None
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if GEMINI_AVAILABLE and GEMINI_API_KEY:
    try:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        print("✅ Gemini Vision API initialized successfully")
    except Exception as e:
        print(f"⚠️  Failed to initialize Gemini: {e}")
        gemini_client = None
else:
    if not GEMINI_AVAILABLE:
        print("ℹ️  Gemini Vision API not available (install: pip install google-genai)")
    elif not GEMINI_API_KEY:
        print("ℹ️  Gemini API key not set (export GEMINI_API_KEY=your_key)")


# Pydantic models
class WebcamFrameRequest(BaseModel):
    frame: str


class VideoUploadResponse(BaseModel):
    success: bool
    output_video: str
    results: dict


class WebcamAnalysisResponse(BaseModel):
    success: bool
    pose_detected: bool
    annotated_frame: Optional[str] = None
    analysis: Optional[dict] = None
    message: Optional[str] = None


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_gemini_feedback(frame: np.ndarray, skill: str, score: float) -> Optional[dict]:
    """
    Get enhanced feedback from Gemini Vision API

    Args:
        frame: Image frame (BGR numpy array)
        skill: Detected gymnastics skill
        score: Current score from pose analysis

    Returns:
        Enhanced feedback dictionary or None
    """
    if not gemini_client:
        return None

    try:
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Encode frame to JPEG
        _, buffer = cv2.imencode('.jpg', frame_rgb)
        image_bytes = buffer.tobytes()

        # Create Gemini prompt
        prompt = f"""You are an expert gymnastics coach analyzing a gymnast's form in real-time.

Current Analysis:
- Detected Skill: {skill}
- Current Score: {score:.1f}/10.0

Please provide:
1. 2-3 specific technical corrections to improve form (be concise and actionable)
2. 1-2 strengths in the current position
3. Any safety concerns or injury risks you observe

Keep feedback brief and focused on immediate actionable improvements."""

        # Call Gemini Vision API
        response = gemini_client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type='image/jpeg',
                ),
                prompt
            ]
        )

        return {
            'gemini_feedback': response.text,
            'source': 'gemini-vision'
        }

    except Exception as e:
        print(f"Gemini API error: {e}")
        return None


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main application page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/upload")
async def upload_video(video: UploadFile = File(...)):
    """Handle video upload and processing"""
    try:
        # Validate file
        if not video.filename:
            raise HTTPException(status_code=400, detail="No file selected")

        if not allowed_file(video.filename):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Allowed: mp4, avi, mov, mkv, webm"
            )

        # Check file size
        contents = await video.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
            )

        # Save uploaded file
        filename = video.filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_filename = f"{timestamp}_{filename}"
        input_path = UPLOAD_FOLDER / safe_filename

        with open(input_path, 'wb') as f:
            f.write(contents)

        # Process video
        output_filename = f"{safe_filename.rsplit('.', 1)[0]}_analyzed.mp4"
        output_path = OUTPUT_FOLDER / output_filename

        print(f"Processing video: {input_path}")
        results = video_processor.process_video(
            str(input_path),
            str(output_path),
            show_preview=False,
            analyze_every_n_frames=1
        )

        # Clean up input file
        input_path.unlink()

        # Prepare response with detailed results
        response_data = {
            'success': True,
            'output_video': f'/api/download/{output_filename}',
            'results': {
                'total_frames': results['total_frames'],
                'analyzed_frames': results['analyzed_frames'],
                'fps': results['fps'],
                'average_score': results['average_score'],
                'best_frame': {
                    'frame_number': results['best_frame'],
                    'score': results['best_score'],
                    'timestamp': f"{results['best_frame'] / results['fps']:.2f}s"
                },
                'worst_frame': {
                    'frame_number': results['worst_frame'],
                    'score': results['worst_score'],
                    'timestamp': f"{results['worst_frame'] / results['fps']:.2f}s"
                },
                'detected_skill': results.get('detected_skill', 'general'),
                'common_errors': results.get('common_errors', [])
            }
        }

        return JSONResponse(content=response_data)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing video: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing video: {str(e)}")


@app.get("/api/download/{filename}")
async def download_video(filename: str):
    """Download processed video"""
    try:
        file_path = OUTPUT_FOLDER / filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        return FileResponse(
            str(file_path),
            media_type="video/mp4",
            filename=filename
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/webcam/analyze")
async def analyze_webcam_frame(request: WebcamFrameRequest):
    """Analyze a single frame from webcam"""
    try:
        if not request.frame:
            raise HTTPException(status_code=400, detail="No frame data provided")

        # Decode base64 image
        frame_data = request.frame.split(',')[1] if ',' in request.frame else request.frame
        frame_bytes = base64.b64decode(frame_data)

        # Convert to numpy array
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            raise HTTPException(status_code=400, detail="Failed to decode frame")

        # Process frame
        result = video_processor.process_frame(frame, draw_annotations=True)

        if not result or not result.get('pose_detected'):
            return WebcamAnalysisResponse(
                success=False,
                pose_detected=False,
                message='No pose detected'
            )

        # Encode annotated frame back to base64
        _, buffer = cv2.imencode('.jpg', result['frame'])
        annotated_base64 = base64.b64encode(buffer).decode('utf-8')

        # Extract data from result
        analysis = result.get('analysis', {})
        feedback = result.get('feedback', {})
        skill = analysis.get('skill', 'general')
        score = analysis.get('score', 0.0)

        # Get enhanced feedback from Gemini Vision API (if available)
        gemini_enhanced = get_gemini_feedback(frame, skill, score)

        # Prepare response data
        analysis_data = {
            'skill': skill,
            'score': score,
            'quality': analysis.get('overall_quality', 'Unknown'),
            'feedback': {
                'strengths': feedback.get('strengths', []),
                'corrections': feedback.get('corrections', [])[:5],  # Top 5
                'tips': feedback.get('tips', [])[:3],  # Top 3
                'warnings': feedback.get('warnings', []),
                'overall': feedback.get('overall', '')
            },
            'angles': result.get('angles', {})
        }

        # Add Gemini feedback if available
        if gemini_enhanced:
            analysis_data['gemini_feedback'] = gemini_enhanced['gemini_feedback']
            analysis_data['feedback_source'] = 'hybrid'  # MediaPipe + Gemini
        else:
            analysis_data['feedback_source'] = 'mediapipe'  # MediaPipe only

        response_data = WebcamAnalysisResponse(
            success=True,
            pose_detected=True,
            annotated_frame=f'data:image/jpeg;base64,{annotated_base64}',
            analysis=analysis_data
        )

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error analyzing frame: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error analyzing frame: {str(e)}")


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'components': {
            'pose_estimator': 'ready',
            'analyzer': 'ready',
            'feedback_generator': 'ready'
        }
    }


@app.get("/api/skills")
async def get_skills():
    """Get list of supported gymnastics skills"""
    from config import SKILL_TEMPLATES

    skills = []
    for skill_name, template in SKILL_TEMPLATES.items():
        skills.append({
            'name': skill_name,
            'display_name': skill_name.replace('_', ' ').title(),
            'description': template.get('description', ''),
            'key_angles': list(template.get('key_angles', {}).keys())
        })

    return {'skills': skills}


if __name__ == '__main__':
    print("=" * 60)
    print("AI GYMNASTICS COACH - WEB APPLICATION")
    print("=" * 60)
    print("Server starting on http://localhost:8000")
    print("Upload videos or use webcam for live analysis")
    print("=" * 60)

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
