"""
Configuration and thresholds for the AI Gymnastics Coach system.
"""

# Pose detection confidence thresholds
MIN_DETECTION_CONFIDENCE = 0.5
MIN_TRACKING_CONFIDENCE = 0.5

# Gymnastics skill templates and ideal angles (in degrees)
# Each skill has key body angles that should be maintained

SKILL_TEMPLATES = {
    "handstand": {
        "name": "Handstand",
        "key_angles": {
            "body_vertical": {"ideal": 180, "tolerance": 15, "description": "Body should be straight and vertical"},
            "shoulder_angle": {"ideal": 180, "tolerance": 10, "description": "Shoulders fully extended"},
            "hip_angle": {"ideal": 180, "tolerance": 10, "description": "Hips fully extended"},
            "knee_angle": {"ideal": 180, "tolerance": 5, "description": "Knees locked"},
        }
    },
    "split": {
        "name": "Split",
        "key_angles": {
            "leg_split_angle": {"ideal": 180, "tolerance": 15, "description": "Legs should form straight line"},
            "front_knee": {"ideal": 180, "tolerance": 5, "description": "Front knee locked"},
            "back_knee": {"ideal": 180, "tolerance": 5, "description": "Back knee locked"},
            "torso_upright": {"ideal": 90, "tolerance": 15, "description": "Torso should be upright"},
        }
    },
    "bridge": {
        "name": "Bridge",
        "key_angles": {
            "shoulder_angle": {"ideal": 180, "tolerance": 20, "description": "Shoulders extended"},
            "hip_elevation": {"ideal": 120, "tolerance": 20, "description": "Hips should be elevated"},
            "knee_angle": {"ideal": 90, "tolerance": 15, "description": "Knees bent at 90 degrees"},
        }
    },
    "pike": {
        "name": "Pike Position",
        "key_angles": {
            "hip_angle": {"ideal": 45, "tolerance": 15, "description": "Tight pike at hips"},
            "knee_angle": {"ideal": 180, "tolerance": 5, "description": "Knees locked straight"},
            "ankle_point": {"ideal": 160, "tolerance": 10, "description": "Toes pointed"},
        }
    },
    "tuck": {
        "name": "Tuck Position",
        "key_angles": {
            "knee_angle": {"ideal": 45, "tolerance": 15, "description": "Knees tight to chest"},
            "hip_angle": {"ideal": 45, "tolerance": 15, "description": "Tight tuck at hips"},
        }
    }
}

# General form criteria
GENERAL_FORM = {
    "pointed_toes": {"threshold": 160, "description": "Toes should be pointed"},
    "straight_arms": {"threshold": 170, "description": "Arms should be straight"},
    "body_alignment": {"threshold": 15, "description": "Body segments should be aligned"},
}

# Injury risk detection thresholds
INJURY_RISK_THRESHOLDS = {
    "knee_hyperextension": 185,  # degrees
    "elbow_hyperextension": 185,
    "spine_over_arch": 45,  # deviation from neutral
    "unstable_landing": 30,  # knee valgus angle
}

# Visualization colors (BGR format for OpenCV)
COLORS = {
    "good": (0, 255, 0),      # Green
    "warning": (0, 165, 255),  # Orange
    "error": (0, 0, 255),      # Red
    "neutral": (255, 255, 255), # White
    "skeleton": (255, 200, 100), # Light blue
}

# Scoring deduction ranges
DEDUCTION_RANGES = {
    "minor": (0, 5),    # 0-5 degrees off: -0.1 points
    "moderate": (5, 15), # 5-15 degrees off: -0.3 points
    "major": (15, 30),   # 15-30 degrees off: -0.5 points
    "severe": (30, 999), # >30 degrees off: -1.0 points
}

DEDUCTION_VALUES = {
    "minor": 0.1,
    "moderate": 0.3,
    "major": 0.5,
    "severe": 1.0,
}
