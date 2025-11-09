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

# Skill Learning Steps - Progressive coaching curriculum
SKILL_LEARNING_STEPS = {
    "handstand": {
        "name": "Handstand",
        "description": "Master the fundamental inverted position with perfect balance and alignment",
        "steps": [
            {
                "name": "Hand Placement",
                "instruction": "Place your hands shoulder-width apart with fingers spread wide",
                "coaching_cue": "Think about creating a strong foundation",
                "requirements": {
                    "shoulder_angle": {
                        "min": 160,
                        "max": 180,
                        "description": "Shoulders engaged",
                        "tolerance": 15
                    }
                },
                "common_mistakes": ["Hands too close together", "Fingers not spread"],
                "visual_cue": "Shoulder-width hand placement"
            },
            {
                "name": "Shoulder Engagement",
                "instruction": "Push strongly through your shoulders, creating a hollow body position",
                "coaching_cue": "Push the floor away from you",
                "requirements": {
                    "shoulder_angle": {
                        "target": 180,
                        "tolerance": 10,
                        "description": "Shoulders fully extended"
                    }
                },
                "common_mistakes": ["Sagging shoulders", "Not pushing through"],
                "visual_cue": "Active shoulder extension"
            },
            {
                "name": "Hip Alignment",
                "instruction": "Keep your hips directly over your shoulders in one straight line",
                "coaching_cue": "Stack your hips over your hands",
                "requirements": {
                    "hip_angle": {
                        "target": 180,
                        "tolerance": 10,
                        "description": "Hips fully extended"
                    },
                    "torso_vertical": {
                        "target": 180,
                        "tolerance": 15,
                        "description": "Body vertical"
                    }
                },
                "common_mistakes": ["Arched back", "Pike at hips"],
                "visual_cue": "Straight body line"
            },
            {
                "name": "Leg Extension",
                "instruction": "Point your toes and lock your knees while maintaining perfect alignment",
                "coaching_cue": "Reach your toes to the ceiling",
                "requirements": {
                    "knee_angle": {
                        "target": 180,
                        "tolerance": 5,
                        "description": "Knees locked"
                    },
                    "left_ankle": {
                        "min": 160,
                        "max": 180,
                        "description": "Toes pointed"
                    }
                },
                "common_mistakes": ["Bent knees", "Flexed feet"],
                "visual_cue": "Pointed toes, straight legs"
            },
            {
                "name": "Complete Handstand",
                "instruction": "Hold the complete handstand position with perfect form",
                "coaching_cue": "One straight line from hands to toes",
                "requirements": {
                    "shoulder_angle": {"target": 180, "tolerance": 10, "description": "Shoulders extended"},
                    "hip_angle": {"target": 180, "tolerance": 10, "description": "Hips extended"},
                    "knee_angle": {"target": 180, "tolerance": 5, "description": "Knees locked"},
                    "torso_vertical": {"target": 180, "tolerance": 10, "description": "Body vertical"}
                },
                "common_mistakes": ["Any deviation from alignment"],
                "visual_cue": "Perfect handstand"
            }
        ]
    },
    "bridge": {
        "name": "Bridge",
        "description": "Develop back flexibility and shoulder mobility safely",
        "steps": [
            {
                "name": "Starting Position",
                "instruction": "Lie on your back with knees bent, feet flat on the floor hip-width apart",
                "coaching_cue": "Set up your foundation first",
                "requirements": {
                    "left_knee": {"min": 80, "max": 100, "description": "Knees bent comfortably"}
                },
                "common_mistakes": ["Feet too close or far"],
                "visual_cue": "Bent knees, flat feet"
            },
            {
                "name": "Hand Placement",
                "instruction": "Place hands by your ears, fingers pointing toward shoulders",
                "coaching_cue": "Hands near your ears, elbows up",
                "requirements": {
                    "left_shoulder": {"min": 100, "max": 140, "description": "Elbows bent ready to push"}
                },
                "common_mistakes": ["Hands too far from head", "Fingers pointing wrong way"],
                "visual_cue": "Hands by ears"
            },
            {
                "name": "Hip Lift",
                "instruction": "Press through your feet to lift your hips toward the ceiling",
                "coaching_cue": "Push your hips up high",
                "requirements": {
                    "hip_angle": {"min": 100, "max": 140, "description": "Hips elevated"},
                    "knee_angle": {"min": 80, "max": 110, "description": "Knees bent"}
                },
                "common_mistakes": ["Not lifting hips enough", "Feet turning out"],
                "visual_cue": "Hips elevated"
            },
            {
                "name": "Shoulder Extension",
                "instruction": "Press through your hands to straighten your arms and open your shoulders",
                "coaching_cue": "Push the floor away",
                "requirements": {
                    "shoulder_angle": {"target": 180, "tolerance": 20, "description": "Shoulders extended"},
                    "left_elbow": {"min": 160, "max": 180, "description": "Arms straightening"}
                },
                "common_mistakes": ["Weak arm push", "Shoulders not opening"],
                "visual_cue": "Straight arms"
            },
            {
                "name": "Full Bridge",
                "instruction": "Hold the full bridge with even weight distribution and open shoulders",
                "coaching_cue": "Create a smooth arch from hands to feet",
                "requirements": {
                    "shoulder_angle": {"target": 180, "tolerance": 20, "description": "Shoulders fully extended"},
                    "hip_angle": {"target": 120, "tolerance": 20, "description": "Hips elevated"},
                    "knee_angle": {"target": 90, "tolerance": 15, "description": "Knees at 90 degrees"}
                },
                "common_mistakes": ["Uneven weight", "Collapsed shoulders"],
                "visual_cue": "Full bridge arch"
            }
        ]
    },
    "split": {
        "name": "Front Split",
        "description": "Achieve full splits with proper alignment and flexibility",
        "steps": [
            {
                "name": "Starting Lunge",
                "instruction": "Start in a low lunge with your front knee bent and back leg extended",
                "coaching_cue": "Long back leg, front knee over ankle",
                "requirements": {
                    "right_knee": {"min": 165, "max": 180, "description": "Back leg straight"}
                },
                "common_mistakes": ["Back knee bent", "Front knee past toes"],
                "visual_cue": "Low lunge position"
            },
            {
                "name": "Front Leg Extension",
                "instruction": "Slowly straighten your front leg while keeping your back leg extended",
                "coaching_cue": "Slide your front heel forward",
                "requirements": {
                    "left_knee": {"target": 180, "tolerance": 10, "description": "Front knee straight"},
                    "right_knee": {"target": 180, "tolerance": 10, "description": "Back knee straight"}
                },
                "common_mistakes": ["Bent front knee", "Turned out back leg"],
                "visual_cue": "Both legs straight"
            },
            {
                "name": "Hip Square",
                "instruction": "Keep your hips square and facing forward as you lower down",
                "coaching_cue": "Both hip bones pointing forward",
                "requirements": {
                    "torso_vertical": {"min": 75, "max": 105, "description": "Upright torso"}
                },
                "common_mistakes": ["Hips turning", "Leaning to one side"],
                "visual_cue": "Square hips"
            },
            {
                "name": "Depth Increase",
                "instruction": "Gradually slide deeper while maintaining leg extension and hip alignment",
                "coaching_cue": "Lower slowly with control",
                "requirements": {
                    "left_knee": {"target": 180, "tolerance": 5, "description": "Front leg locked"},
                    "right_knee": {"target": 180, "tolerance": 5, "description": "Back leg locked"},
                    "left_hip": {"min": 160, "max": 180, "description": "Front hip extended"}
                },
                "common_mistakes": ["Rushing", "Bouncing"],
                "visual_cue": "Controlled lowering"
            },
            {
                "name": "Full Split",
                "instruction": "Achieve full split with both legs straight and hips square",
                "coaching_cue": "Relax into the stretch, breathe deeply",
                "requirements": {
                    "left_knee": {"target": 180, "tolerance": 5, "description": "Front knee locked"},
                    "right_knee": {"target": 180, "tolerance": 5, "description": "Back knee locked"},
                    "torso_vertical": {"target": 90, "tolerance": 15, "description": "Torso upright"}
                },
                "common_mistakes": ["Any bent legs", "Twisted hips"],
                "visual_cue": "Perfect split"
            }
        ]
    },
    "pike": {
        "name": "Pike Position",
        "description": "Master the tight pike position fundamental to many gymnastics skills",
        "steps": [
            {
                "name": "Seated Pike",
                "instruction": "Sit with legs extended straight in front, toes pointed",
                "coaching_cue": "Press knees down into the floor",
                "requirements": {
                    "knee_angle": {"target": 180, "tolerance": 10, "description": "Legs straight"}
                },
                "common_mistakes": ["Bent knees", "Relaxed feet"],
                "visual_cue": "Straight legs seated"
            },
            {
                "name": "Forward Fold",
                "instruction": "Reach forward and fold at the hips, keeping your back straight",
                "coaching_cue": "Fold from your hips, not your back",
                "requirements": {
                    "hip_angle": {"min": 30, "max": 60, "description": "Folding at hips"}
                },
                "common_mistakes": ["Rounding back", "Bending knees"],
                "visual_cue": "Hip hinge"
            },
            {
                "name": "Toe Point",
                "instruction": "Actively point your toes while maintaining the fold",
                "coaching_cue": "Push through your ankles",
                "requirements": {
                    "left_ankle": {"min": 155, "max": 180, "description": "Toes pointed"}
                },
                "common_mistakes": ["Flexed feet", "Relaxed ankles"],
                "visual_cue": "Pointed toes"
            },
            {
                "name": "Deep Pike",
                "instruction": "Deepen the pike fold while keeping legs completely straight",
                "coaching_cue": "Chest to thighs, nose to knees",
                "requirements": {
                    "hip_angle": {"target": 45, "tolerance": 15, "description": "Tight pike"},
                    "knee_angle": {"target": 180, "tolerance": 5, "description": "Locked knees"}
                },
                "common_mistakes": ["Bent knees", "Forced stretch"],
                "visual_cue": "Tight compression"
            }
        ]
    },
    "tuck": {
        "name": "Tuck Position",
        "description": "Perfect the tight tuck position used in flips and jumps",
        "steps": [
            {
                "name": "Knee Tuck",
                "instruction": "Bring your knees toward your chest while seated or standing",
                "coaching_cue": "Pull knees tight to chest",
                "requirements": {
                    "knee_angle": {"min": 30, "max": 60, "description": "Knees bent"}
                },
                "common_mistakes": ["Loose tuck", "Legs apart"],
                "visual_cue": "Knees to chest"
            },
            {
                "name": "Hip Compression",
                "instruction": "Compress at the hips, bringing chest down to thighs",
                "coaching_cue": "Make yourself as small as possible",
                "requirements": {
                    "hip_angle": {"min": 30, "max": 60, "description": "Hip compression"}
                },
                "common_mistakes": ["Not compressing enough", "Back not rounded"],
                "visual_cue": "Tight ball"
            },
            {
                "name": "Tight Tuck Hold",
                "instruction": "Hold the tightest tuck position you can maintain",
                "coaching_cue": "Squeeze everything tight",
                "requirements": {
                    "knee_angle": {"target": 45, "tolerance": 15, "description": "Knees tight to chest"},
                    "hip_angle": {"target": 45, "tolerance": 15, "description": "Maximum compression"}
                },
                "common_mistakes": ["Relaxing", "Opening up"],
                "visual_cue": "Perfect tuck"
            }
        ]
    }
}
