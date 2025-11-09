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
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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
from coaching_engine import CoachingEngine

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

# Templates configuration (must be before routes)
templates = Jinja2Templates(directory="templates")

# Initialize video processor (it creates its own pose estimator, analyzer, and feedback generator)
video_processor = VideoProcessor()

# Initialize coaching engine
coaching_engine = CoachingEngine()

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


class CoachingStartRequest(BaseModel):
    skill: str
    session_id: Optional[str] = "default"


class CoachingFrameRequest(BaseModel):
    frame: str
    session_id: Optional[str] = "default"


class CoachingAdvanceRequest(BaseModel):
    session_id: Optional[str] = "default"


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_gemini_feedback(frame: np.ndarray, skill: str, score: float) -> Optional[dict]:
    """
    Get enhanced feedback from Gemini Vision API for real-time analysis

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


def get_gemini_video_analysis(
    video_path: str,
    results: dict,
    best_frame: Optional[np.ndarray] = None,
    worst_frame: Optional[np.ndarray] = None
) -> Optional[dict]:
    """
    Get comprehensive Gemini analysis for uploaded video performance

    Args:
        video_path: Path to analyzed video
        results: Analysis results from video processor
        best_frame: Best performing frame (optional)
        worst_frame: Worst performing frame (optional)

    Returns:
        Comprehensive feedback dictionary or None
    """
    if not gemini_client:
        return None

    try:
        # Prepare frames for analysis
        frames_data = []

        # Add best frame if available
        if best_frame is not None:
            frame_rgb = cv2.cvtColor(best_frame, cv2.COLOR_BGR2RGB)
            _, buffer = cv2.imencode('.jpg', frame_rgb)
            frames_data.append({
                'data': buffer.tobytes(),
                'label': 'Best Performance Frame'
            })

        # Add worst frame if available
        if worst_frame is not None:
            frame_rgb = cv2.cvtColor(worst_frame, cv2.COLOR_BGR2RGB)
            _, buffer = cv2.imencode('.jpg', frame_rgb)
            frames_data.append({
                'data': buffer.tobytes(),
                'label': 'Frame Needing Improvement'
            })

        if not frames_data:
            return None

        # Build comprehensive prompt
        skill = results.get('detected_skill', 'general gymnastics')
        avg_score = results.get('average_score', 0.0)
        best_score = results.get('best_score', 0.0)
        worst_score = results.get('worst_score', 0.0)
        common_errors = results.get('common_errors', {})

        # Format common errors
        error_list = "\n".join([f"  - {error}: {count} occurrences"
                                for error, count in sorted(common_errors.items(),
                                                          key=lambda x: x[1],
                                                          reverse=True)[:5]])

        prompt = f"""You are an Olympic-level gymnastics coach analyzing a complete performance video.

## Performance Summary
- Skill: {skill.upper()}
- Average Score: {avg_score:.1f}/10.0
- Best Score: {best_score:.1f}/10.0
- Worst Score: {worst_score:.1f}/10.0
- Total Frames Analyzed: {results.get('analyzed_frames', 0)}

## Most Common Errors
{error_list if error_list else "  None detected"}

## Analysis Request
Based on the attached frames (best and worst moments), please provide:

1. **Overall Performance Assessment** (2-3 sentences)
   - What is their current skill level?
   - What stands out about their performance?

2. **Key Strengths** (2-3 bullet points)
   - What are they doing well consistently?
   - Which technical elements are strong?

3. **Priority Corrections** (3-4 bullet points)
   - What are the most important things to fix?
   - Be specific and actionable
   - Prioritize by impact on score and safety

4. **Training Recommendations** (2-3 bullet points)
   - What drills or exercises should they focus on?
   - How can they improve fastest?

5. **Safety Notes** (if any)
   - Any injury risks you observe?
   - Form issues that could lead to injury?

Keep feedback practical, encouraging, and focused on improvement. Be direct but supportive.
"""

        # Build content list for Gemini
        content_parts = []

        # Add frames
        for frame_info in frames_data:
            content_parts.append(types.Part.from_bytes(
                data=frame_info['data'],
                mime_type='image/jpeg'
            ))

        # Add prompt
        content_parts.append(prompt)

        # Call Gemini Vision API
        response = gemini_client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=content_parts
        )

        return {
            'comprehensive_feedback': response.text,
            'source': 'gemini-video-analysis',
            'analyzed_skill': skill,
            'scores': {
                'average': avg_score,
                'best': best_score,
                'worst': worst_score
            }
        }

    except Exception as e:
        print(f"Gemini video analysis error: {e}")
        import traceback
        traceback.print_exc()
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
            analyze_every_n_frames=1,
            capture_key_frames=True  # Capture best/worst frames for Gemini
        )

        # Clean up input file
        input_path.unlink()

        # Get comprehensive Gemini feedback if available
        gemini_analysis = None
        if gemini_client and results.get('best_frame_image') is not None:
            print("Generating comprehensive Gemini feedback...")
            gemini_analysis = get_gemini_video_analysis(
                str(input_path),
                results,
                best_frame=results.get('best_frame_image'),
                worst_frame=results.get('worst_frame_image')
            )

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
                    'frame_number': results.get('best_frame_number', 0),
                    'score': results.get('best_score', 0.0),
                    'timestamp': results.get('best_timestamp', '0.00s')
                },
                'worst_frame': {
                    'frame_number': results.get('worst_frame_number', 0),
                    'score': results.get('worst_score', 0.0),
                    'timestamp': results.get('worst_timestamp', '0.00s')
                },
                'detected_skill': results.get('skill_detected', 'general'),
                'common_errors': results.get('common_errors', [])
            }
        }

        # Add Gemini comprehensive feedback if available
        if gemini_analysis:
            response_data['gemini_analysis'] = gemini_analysis
            print("✅ Gemini comprehensive feedback generated")

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


@app.get("/api/coaching/skills")
async def get_coaching_skills():
    """Get list of skills available for coaching with learning steps"""
    from config import SKILL_LEARNING_STEPS

    skills = []
    for skill_name, skill_data in SKILL_LEARNING_STEPS.items():
        skills.append({
            'name': skill_name,
            'display_name': skill_data['name'],
            'description': skill_data['description'],
            'total_steps': len(skill_data['steps']),
            'difficulty': skill_data.get('difficulty', 'advanced')  # Default to advanced if not specified
        })

    return {'skills': skills}


@app.post("/api/coaching/start")
async def start_coaching(request: CoachingStartRequest):
    """Start a new coaching session for a skill"""
    try:
        result = coaching_engine.start_coaching_session(
            skill=request.skill,
            session_id=request.session_id
        )

        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed to start session'))

        return result

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error starting coaching session: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/coaching/analyze")
async def analyze_coaching_frame(request: CoachingFrameRequest):
    """Analyze a frame for step-by-step coaching"""
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

        # Get current step info
        step_info_result = coaching_engine.get_current_step(request.session_id)
        if not step_info_result:
            raise HTTPException(status_code=400, detail="No active coaching session")

        if step_info_result.get('completed'):
            return {
                'success': True,
                'completed': True,
                'message': step_info_result['message']
            }

        # Process frame with pose estimation
        result = video_processor.process_frame(frame, draw_annotations=True)

        if not result.get('pose_detected'):
            return {
                'success': False,
                'pose_detected': False,
                'message': 'No pose detected. Make sure you are fully visible in the camera.'
            }

        # Evaluate step completion
        angles = result.get('angles', {})
        evaluation = coaching_engine.evaluate_step_completion(
            angles=angles,
            session_id=request.session_id
        )

        # Get Gemini coaching feedback
        step_info = step_info_result['step_info']
        gemini_coaching = None

        if gemini_client:
            try:
                skill = step_info_result['skill']
                prompt = coaching_engine.get_gemini_coaching_prompt(
                    skill=skill,
                    step_info=step_info,
                    angles=angles,
                    evaluation=evaluation
                )

                # Get Gemini feedback
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                _, buffer = cv2.imencode('.jpg', frame_rgb)
                image_bytes = buffer.tobytes()

                response = gemini_client.models.generate_content(
                    model='gemini-2.0-flash-exp',
                    contents=[
                        types.Part.from_bytes(
                            data=image_bytes,
                            mime_type='image/jpeg'
                        ),
                        prompt
                    ]
                )

                gemini_coaching = response.text

            except Exception as e:
                print(f"Gemini coaching error: {e}")
                gemini_coaching = None

        # Encode annotated frame
        _, buffer = cv2.imencode('.jpg', result['frame'])
        annotated_base64 = base64.b64encode(buffer).decode('utf-8')

        # Build response
        response_data = {
            'success': True,
            'pose_detected': True,
            'annotated_frame': f'data:image/jpeg;base64,{annotated_base64}',
            'step_info': {
                'step_number': step_info_result['step_number'],
                'total_steps': step_info_result['total_steps'],
                'name': step_info['name'],
                'instruction': step_info['instruction'],
                'coaching_cue': step_info['coaching_cue']
            },
            'evaluation': {
                'step_completed': evaluation['step_completed'],
                'checks': evaluation['checks'],
                'feedback': evaluation['feedback'],
                'attempts': evaluation['attempts']
            }
        }

        # Add Gemini coaching if available
        if gemini_coaching:
            response_data['gemini_coaching'] = gemini_coaching
            response_data['audio_text'] = gemini_coaching  # For TTS
        else:
            response_data['audio_text'] = evaluation['feedback']  # Fallback to basic feedback

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error analyzing coaching frame: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/coaching/next-step")
async def advance_coaching_step(request: CoachingAdvanceRequest):
    """Advance to the next step in the coaching progression"""
    try:
        result = coaching_engine.advance_to_next_step(request.session_id)

        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed to advance'))

        return result

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error advancing coaching step: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# Mount static files AFTER all routes are defined
app.mount("/static", StaticFiles(directory="static"), name="static")


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
