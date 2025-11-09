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

# Templates configuration (must be before routes)
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


class TrainingInstructionRequest(BaseModel):
    skill: str


class TrainingInstructionResponse(BaseModel):
    success: bool
    skill: str
    instruction: str
    preparation_time: int  # seconds


class TrainingAssessmentRequest(BaseModel):
    skill: str
    frame: str


class TrainingAssessmentResponse(BaseModel):
    success: bool
    assessment: str
    is_correct: bool
    corrections: list[str]
    encouragement: str


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


@app.post("/api/training/instruction")
async def get_training_instruction(request: TrainingInstructionRequest):
    """Get instruction for learning a gymnastics skill"""
    try:
        skill = request.skill
        skill_display = skill.replace('_', ' ').title()

        # If Gemini is available, use it for better instructions
        if gemini_client:
            try:
                # Check if it's a simple demo action or gymnastics
                is_simple_action = skill in ['sitting_posture', 'standing_straight', 'arms_raised', 'thumbs_up', 't_pose', 'stretching']

                if is_simple_action:
                    prompt = f"""You are a friendly coach helping someone demonstrate a simple action: {skill_display}.

This is for a software demo - the person is NOT an athlete, just testing the AI system. Provide brief, easy-to-follow instructions:
1. Be casual and encouraging
2. Explain what to do in simple terms (2-3 sentences)
3. Mention this is easy and perfect for demos
4. Keep it very short and conversational (will be read aloud)

Start with "Let's try {skill_display}!" Keep it under 50 words."""
                else:
                    prompt = f"""You are an expert gymnastics coach teaching a beginner how to perform a {skill_display}.

Provide clear, step-by-step instructions for how to perform this skill. Your instruction should:
1. Be encouraging and supportive
2. Explain the key body positions (where hands, feet, hips should be)
3. Include 3-5 specific, actionable steps
4. Mention important safety considerations
5. Be spoken in a friendly, coaching voice (this will be read aloud)

Keep it concise (2-3 short paragraphs max). Start with "Let's learn the {skill_display}!" """

                response = gemini_client.models.generate_content(
                    model='gemini-2.0-flash-exp',
                    contents=[prompt]
                )

                instruction = response.text
            except Exception as e:
                print(f"Gemini error for instruction: {e}")
                instruction = get_fallback_instruction(skill)
        else:
            instruction = get_fallback_instruction(skill)

        return TrainingInstructionResponse(
            success=True,
            skill=skill,
            instruction=instruction,
            preparation_time=5  # 5 seconds to get ready
        )

    except Exception as e:
        print(f"Error getting instruction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/training/assess")
async def assess_training_attempt(request: TrainingAssessmentRequest):
    """Assess user's attempt at performing a skill using Gemini Vision"""
    try:
        if not gemini_client:
            raise HTTPException(
                status_code=503,
                detail="Gemini Vision API not available. Please set GEMINI_API_KEY in .env file"
            )

        skill = request.skill
        skill_display = skill.replace('_', ' ').title()

        # Decode base64 image
        frame_data = request.frame.split(',')[1] if ',' in request.frame else request.frame
        frame_bytes = base64.b64decode(frame_data)

        # Convert to numpy array
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            raise HTTPException(status_code=400, detail="Failed to decode frame")

        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Encode frame to JPEG
        _, buffer = cv2.imencode('.jpg', frame_rgb)
        image_bytes = buffer.tobytes()

        # Create assessment prompt based on skill type
        is_simple_action = skill in ['sitting_posture', 'standing_straight', 'arms_raised', 'thumbs_up', 't_pose', 'stretching']

        if is_simple_action:
            prompt = f"""You are analyzing someone demonstrating {skill_display} for a software demo.

Give quick, friendly, real-time feedback:
1. Are they doing it correctly? (YES/NO)
2. One simple tip to improve (if needed)
3. Brief encouragement (1 sentence)

Keep it SHORT and conversational - this is continuous feedback. Format:
CORRECT: [YES/NO]
TIP: [one quick tip or "Looking good!"]
FEEDBACK: [one encouraging sentence]

Be casual and positive - they're just testing the system!"""
        else:
            prompt = f"""You are an expert gymnastics coach assessing a student's attempt at performing a {skill_display}.

Analyze the image and provide:
1. Whether they are performing the skill correctly (YES/NO)
2. 2-3 specific corrections if needed (what to fix)
3. 1-2 things they're doing well
4. Encouraging feedback to keep them motivated

Format your response as:
CORRECT: [YES/NO]
CORRECTIONS:
- [correction 1 if needed]
- [correction 2 if needed]
STRENGTHS:
- [strength 1]
- [strength 2]
ENCOURAGEMENT: [motivating message]

Be supportive, specific, and actionable. This is a learning environment, not a competition."""

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

        # Parse response
        assessment_text = response.text
        is_correct = 'CORRECT: YES' in assessment_text.upper()

        # Extract corrections
        corrections = []
        if 'CORRECTIONS:' in assessment_text:
            corrections_section = assessment_text.split('CORRECTIONS:')[1].split('STRENGTHS:')[0]
            corrections = [line.strip('- ').strip() for line in corrections_section.split('\n') if line.strip().startswith('-')]

        # Extract encouragement
        encouragement = "Keep practicing! You're doing great!"
        if 'ENCOURAGEMENT:' in assessment_text:
            encouragement = assessment_text.split('ENCOURAGEMENT:')[1].strip().split('\n')[0]

        return TrainingAssessmentResponse(
            success=True,
            assessment=assessment_text,
            is_correct=is_correct,
            corrections=corrections if corrections else ["Great job! Keep practicing to maintain consistency."],
            encouragement=encouragement
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in training assessment: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


def get_fallback_instruction(skill: str) -> str:
    """Get fallback instruction when Gemini is not available"""
    instructions = {
        'sitting_posture': """Let's practice Good Sitting Posture!

Sit comfortably in your chair with your feet flat on the floor. Keep your back straight and shoulders relaxed. Your head should be level, not tilted forward or back. Place your hands comfortably on your desk or lap.

Key points: Shoulders should be back and down, not hunched. Your screen should be at eye level. Keep a small gap between the back of your knees and the chair seat. This is perfect for developers who sit all day!""",

        'standing_straight': """Let's practice Standing Straight!

Stand with your feet shoulder-width apart. Distribute your weight evenly on both feet. Keep your shoulders back and relaxed, not tensed up. Your head should be level, chin parallel to the ground.

Focus on: Imagine a string pulling you up from the top of your head. Keep your core engaged but breathe naturally. Arms should hang naturally at your sides. This is great posture for standing meetings!""",

        'arms_raised': """Let's practice Arms Raised!

Start standing straight. Slowly raise both arms straight up overhead, reaching toward the ceiling. Keep your arms straight and parallel to each other. Your palms can face forward or toward each other.

Remember: Keep your shoulders relaxed, don't shrug them up toward your ears. Your core should stay engaged. This is a simple movement that's easy to demo and great for stretching!""",

        'thumbs_up': """Let's try Thumbs Up!

Simply raise one or both hands and give a thumbs up gesture! Keep your hand at chest height or higher so the camera can see it clearly. Make sure your thumb is clearly extended upward.

This is perfect for: Testing gesture recognition, simple demos, and showing approval. Super easy for anyone to do!""",

        't_pose': """Let's practice the T-Pose!

Stand straight with your feet shoulder-width apart. Extend both arms out to your sides, parallel to the ground. Your body should form a 'T' shape when viewed from the front.

Key points: Keep your arms straight and level with your shoulders. Palms can face down or forward. This is a classic pose used in gaming and animation - perfect for demos!""",

        'stretching': """Let's do a Simple Desk Stretch!

Sit or stand comfortably. Reach both arms overhead and interlace your fingers. Gently lean to one side for a few seconds, then the other. You can also do shoulder rolls: roll your shoulders backward in a circular motion.

Great for: Desk workers, developers, and anyone who needs a quick stretch break. Easy to demonstrate and feels good too!"""
    }

    return instructions.get(skill, f"""Let's practice {skill.replace('_', ' ').title()}!

This is a simple action that anyone can do - perfect for demos and testing! Just follow the instructions, position yourself so the camera can see you clearly, and let the AI coach guide you.

Remember: No athletic skills needed! This is designed to be easy and fun to demonstrate.""")


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
