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

from video_processor import VideoProcessor
from pose_estimator import PoseEstimator
from gymnastics_analyzer import GymnasticsAnalyzer
from feedback_generator import FeedbackGenerator

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

# Initialize components
pose_estimator = PoseEstimator()
analyzer = GymnasticsAnalyzer()
feedback_generator = FeedbackGenerator()
video_processor = VideoProcessor(pose_estimator, analyzer, feedback_generator)


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

        if result is None:
            return WebcamAnalysisResponse(
                success=False,
                pose_detected=False,
                message='No pose detected'
            )

        # Encode annotated frame back to base64
        _, buffer = cv2.imencode('.jpg', result['annotated_frame'])
        annotated_base64 = base64.b64encode(buffer).decode('utf-8')

        # Prepare response
        response_data = WebcamAnalysisResponse(
            success=True,
            pose_detected=True,
            annotated_frame=f'data:image/jpeg;base64,{annotated_base64}',
            analysis={
                'skill': result['skill'],
                'score': result['score'],
                'quality': result['quality'],
                'feedback': {
                    'strengths': result['feedback']['strengths'],
                    'corrections': result['feedback']['corrections'][:5],  # Top 5
                    'tips': result['feedback']['tips'][:3],  # Top 3
                    'warnings': result['feedback']['warnings'],
                    'overall': result['feedback']['overall']
                },
                'angles': result['angles']
            }
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
