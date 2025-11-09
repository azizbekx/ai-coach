"""
Pose estimation using MediaPipe for gymnastics analysis.
"""

import cv2
import mediapipe as mp
import numpy as np
from typing import Optional, Dict, List, Tuple
from config import MIN_DETECTION_CONFIDENCE, MIN_TRACKING_CONFIDENCE


class PoseEstimator:
    """Wrapper for MediaPipe Pose detection optimized for gymnastics."""

    def __init__(self):
        """Initialize MediaPipe Pose detector."""
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=2,  # Highest accuracy
            enable_segmentation=False,
            min_detection_confidence=MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=MIN_TRACKING_CONFIDENCE
        )

    def detect_pose(self, frame: np.ndarray) -> Optional[Dict]:
        """
        Detect pose landmarks in a frame.

        Args:
            frame: Input image frame (BGR format)

        Returns:
            Dictionary containing landmarks and metadata, or None if detection fails
        """
        # Convert BGR to RGB for MediaPipe
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False

        # Detect pose
        results = self.pose.process(image_rgb)

        if not results.pose_landmarks:
            return None

        # Extract landmark coordinates
        landmarks = []
        h, w = frame.shape[:2]

        for landmark in results.pose_landmarks.landmark:
            landmarks.append({
                'x': landmark.x * w,
                'y': landmark.y * h,
                'z': landmark.z,
                'visibility': landmark.visibility
            })

        return {
            'landmarks': landmarks,
            'pose_landmarks': results.pose_landmarks,
            'frame_shape': (h, w)
        }

    def calculate_angle(self, p1: Dict, p2: Dict, p3: Dict) -> float:
        """
        Calculate angle between three points.

        Args:
            p1, p2, p3: Points as dictionaries with 'x' and 'y' keys
            p2 is the vertex of the angle

        Returns:
            Angle in degrees
        """
        # Convert to numpy arrays
        a = np.array([p1['x'], p1['y']])
        b = np.array([p2['x'], p2['y']])
        c = np.array([p3['x'], p3['y']])

        # Calculate vectors
        ba = a - b
        bc = c - b

        # Calculate angle using dot product
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        cosine_angle = np.clip(cosine_angle, -1.0, 1.0)  # Handle floating point errors
        angle = np.arccos(cosine_angle)

        return np.degrees(angle)

    def get_landmark(self, landmarks: List[Dict], index: int) -> Optional[Dict]:
        """
        Safely get a landmark by index.

        Args:
            landmarks: List of landmark dictionaries
            index: MediaPipe landmark index

        Returns:
            Landmark dictionary or None if not available
        """
        if 0 <= index < len(landmarks):
            landmark = landmarks[index]
            # Only return if visibility is high enough
            if landmark['visibility'] > 0.5:
                return landmark
        return None

    def calculate_body_angles(self, landmarks: List[Dict]) -> Dict[str, float]:
        """
        Calculate key body angles for gymnastics analysis.

        Args:
            landmarks: List of pose landmarks

        Returns:
            Dictionary of angle measurements
        """
        angles = {}

        # MediaPipe landmark indices
        LEFT_SHOULDER = 11
        RIGHT_SHOULDER = 12
        LEFT_ELBOW = 13
        RIGHT_ELBOW = 14
        LEFT_WRIST = 15
        RIGHT_WRIST = 16
        LEFT_HIP = 23
        RIGHT_HIP = 24
        LEFT_KNEE = 25
        RIGHT_KNEE = 26
        LEFT_ANKLE = 27
        RIGHT_ANKLE = 28
        LEFT_HEEL = 29
        RIGHT_HEEL = 30
        LEFT_FOOT_INDEX = 31
        RIGHT_FOOT_INDEX = 32

        # Left elbow angle
        l_shoulder = self.get_landmark(landmarks, LEFT_SHOULDER)
        l_elbow = self.get_landmark(landmarks, LEFT_ELBOW)
        l_wrist = self.get_landmark(landmarks, LEFT_WRIST)
        if all([l_shoulder, l_elbow, l_wrist]):
            angles['left_elbow'] = self.calculate_angle(l_shoulder, l_elbow, l_wrist)

        # Right elbow angle
        r_shoulder = self.get_landmark(landmarks, RIGHT_SHOULDER)
        r_elbow = self.get_landmark(landmarks, RIGHT_ELBOW)
        r_wrist = self.get_landmark(landmarks, RIGHT_WRIST)
        if all([r_shoulder, r_elbow, r_wrist]):
            angles['right_elbow'] = self.calculate_angle(r_shoulder, r_elbow, r_wrist)

        # Left shoulder angle
        l_hip = self.get_landmark(landmarks, LEFT_HIP)
        if all([l_elbow, l_shoulder, l_hip]):
            angles['left_shoulder'] = self.calculate_angle(l_elbow, l_shoulder, l_hip)

        # Right shoulder angle
        r_hip = self.get_landmark(landmarks, RIGHT_HIP)
        if all([r_elbow, r_shoulder, r_hip]):
            angles['right_shoulder'] = self.calculate_angle(r_elbow, r_shoulder, r_hip)

        # Left hip angle
        l_knee = self.get_landmark(landmarks, LEFT_KNEE)
        if all([l_shoulder, l_hip, l_knee]):
            angles['left_hip'] = self.calculate_angle(l_shoulder, l_hip, l_knee)

        # Right hip angle
        r_knee = self.get_landmark(landmarks, RIGHT_KNEE)
        if all([r_shoulder, r_hip, r_knee]):
            angles['right_hip'] = self.calculate_angle(r_shoulder, r_hip, r_knee)

        # Left knee angle
        l_ankle = self.get_landmark(landmarks, LEFT_ANKLE)
        if all([l_hip, l_knee, l_ankle]):
            angles['left_knee'] = self.calculate_angle(l_hip, l_knee, l_ankle)

        # Right knee angle
        r_ankle = self.get_landmark(landmarks, RIGHT_ANKLE)
        if all([r_hip, r_knee, r_ankle]):
            angles['right_knee'] = self.calculate_angle(r_hip, r_knee, r_ankle)

        # Left ankle angle (toe point)
        l_heel = self.get_landmark(landmarks, LEFT_HEEL)
        l_foot = self.get_landmark(landmarks, LEFT_FOOT_INDEX)
        if all([l_knee, l_ankle, l_foot]):
            angles['left_ankle'] = self.calculate_angle(l_knee, l_ankle, l_foot)

        # Right ankle angle (toe point)
        r_heel = self.get_landmark(landmarks, RIGHT_HEEL)
        r_foot = self.get_landmark(landmarks, RIGHT_FOOT_INDEX)
        if all([r_knee, r_ankle, r_foot]):
            angles['right_ankle'] = self.calculate_angle(r_knee, r_ankle, r_foot)

        # Body alignment - calculate if torso is vertical
        if all([l_shoulder, r_shoulder, l_hip, r_hip]):
            # Average shoulder and hip positions
            shoulder_center = {
                'x': (l_shoulder['x'] + r_shoulder['x']) / 2,
                'y': (l_shoulder['y'] + r_shoulder['y']) / 2
            }
            hip_center = {
                'x': (l_hip['x'] + r_hip['x']) / 2,
                'y': (l_hip['y'] + r_hip['y']) / 2
            }

            # Calculate angle from vertical (0 degrees = perfectly vertical)
            dy = hip_center['y'] - shoulder_center['y']
            dx = hip_center['x'] - shoulder_center['x']
            angle_from_vertical = abs(np.degrees(np.arctan2(dx, dy)))
            angles['torso_vertical'] = 180 - angle_from_vertical

        return angles

    def draw_pose(self, frame: np.ndarray, pose_data: Dict, color: Tuple[int, int, int] = None) -> np.ndarray:
        """
        Draw pose skeleton on frame.

        Args:
            frame: Input frame
            pose_data: Pose data from detect_pose()
            color: Optional BGR color tuple

        Returns:
            Frame with pose drawn
        """
        if pose_data is None or 'pose_landmarks' not in pose_data:
            return frame

        frame_copy = frame.copy()

        # Draw landmarks
        self.mp_drawing.draw_landmarks(
            frame_copy,
            pose_data['pose_landmarks'],
            self.mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style()
        )

        return frame_copy

    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, 'pose'):
            self.pose.close()
