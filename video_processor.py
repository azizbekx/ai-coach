"""
Video processing pipeline for gymnastics analysis.
"""

import cv2
import numpy as np
from typing import Optional, Callable, Dict, List
from pathlib import Path

from pose_estimator import PoseEstimator
from gymnastics_analyzer import GymnasticsAnalyzer
from feedback_generator import FeedbackGenerator
from config import COLORS


class VideoProcessor:
    """Processes videos and performs real-time gymnastics analysis."""

    def __init__(self):
        """Initialize video processor with all components."""
        self.pose_estimator = PoseEstimator()
        self.analyzer = GymnasticsAnalyzer()
        self.feedback_generator = FeedbackGenerator()
        self.colors = COLORS

    def process_video(
        self,
        video_path: str,
        output_path: Optional[str] = None,
        show_preview: bool = False,
        analyze_every_n_frames: int = 1,
        progress_callback: Optional[Callable] = None
    ) -> Dict:
        """
        Process a video file and generate analysis.

        Args:
            video_path: Path to input video
            output_path: Optional path for output video with annotations
            show_preview: Whether to show live preview
            analyze_every_n_frames: Analyze every N frames (1 = all frames)
            progress_callback: Optional callback function for progress updates

        Returns:
            Dictionary with analysis results and statistics
        """
        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")

        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Setup video writer if output requested
        writer = None
        if output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        # Analysis tracking
        frame_analyses = []
        frame_count = 0
        best_frame = None
        best_score = 0.0
        worst_frame = None
        worst_score = 10.0

        print(f"Processing video: {video_path}")
        print(f"Total frames: {total_frames}, FPS: {fps}")
        print(f"Resolution: {width}x{height}")
        print("-" * 60)

        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                frame_count += 1

                # Analyze frame
                should_analyze = (frame_count - 1) % analyze_every_n_frames == 0

                if should_analyze:
                    # Detect pose
                    pose_data = self.pose_estimator.detect_pose(frame)

                    if pose_data:
                        # Calculate angles
                        angles = self.pose_estimator.calculate_body_angles(pose_data['landmarks'])

                        # Analyze form
                        analysis = self.analyzer.analyze_form(angles)
                        analysis['frame_number'] = frame_count
                        analysis['timestamp'] = frame_count / fps

                        frame_analyses.append(analysis)

                        # Track best/worst frames
                        if analysis['score'] > best_score:
                            best_score = analysis['score']
                            best_frame = {
                                'frame_number': frame_count,
                                'analysis': analysis,
                                'timestamp': frame_count / fps
                            }

                        if analysis['score'] < worst_score:
                            worst_score = analysis['score']
                            worst_frame = {
                                'frame_number': frame_count,
                                'analysis': analysis,
                                'timestamp': frame_count / fps
                            }

                        # Generate feedback
                        feedback = self.feedback_generator.generate_feedback(analysis)

                        # Draw annotations on frame
                        annotated_frame = self._draw_annotations(
                            frame.copy(),
                            pose_data,
                            analysis,
                            feedback
                        )
                    else:
                        annotated_frame = frame.copy()
                        self._draw_text(
                            annotated_frame,
                            "No pose detected",
                            (50, 50),
                            self.colors['error']
                        )
                else:
                    annotated_frame = frame.copy()

                # Write frame
                if writer:
                    writer.write(annotated_frame)

                # Show preview
                if show_preview:
                    cv2.imshow('Gymnastics Analysis', annotated_frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

                # Progress callback
                if progress_callback and frame_count % 30 == 0:
                    progress = (frame_count / total_frames) * 100
                    progress_callback(progress, frame_count, total_frames)

        finally:
            cap.release()
            if writer:
                writer.release()
            if show_preview:
                cv2.destroyAllWindows()

        # Compile results
        results = self._compile_results(
            frame_analyses,
            best_frame,
            worst_frame,
            total_frames,
            fps
        )

        print("\n" + "=" * 60)
        print("PROCESSING COMPLETE")
        print("=" * 60)
        print(f"Analyzed {len(frame_analyses)} frames")
        print(f"Average score: {results['average_score']:.2f}/10.0")
        print(f"Best score: {results['best_score']:.2f} (frame {results['best_frame_number']})")
        print(f"Worst score: {results['worst_score']:.2f} (frame {results['worst_frame_number']})")

        if output_path:
            print(f"\nOutput saved to: {output_path}")

        return results

    def process_frame(self, frame: np.ndarray, draw_annotations: bool = True) -> Dict:
        """
        Process a single frame.

        Args:
            frame: Input frame
            draw_annotations: Whether to draw annotations on frame

        Returns:
            Dictionary with analysis and annotated frame
        """
        # Detect pose
        pose_data = self.pose_estimator.detect_pose(frame)

        if not pose_data:
            return {
                'pose_detected': False,
                'frame': frame,
                'analysis': None,
                'feedback': None
            }

        # Calculate angles
        angles = self.pose_estimator.calculate_body_angles(pose_data['landmarks'])

        # Analyze form
        analysis = self.analyzer.analyze_form(angles)

        # Generate feedback
        feedback = self.feedback_generator.generate_feedback(analysis)

        # Draw annotations
        annotated_frame = frame
        if draw_annotations:
            annotated_frame = self._draw_annotations(
                frame.copy(),
                pose_data,
                analysis,
                feedback
            )

        return {
            'pose_detected': True,
            'frame': annotated_frame,
            'pose_data': pose_data,
            'angles': angles,
            'analysis': analysis,
            'feedback': feedback
        }

    def _draw_annotations(
        self,
        frame: np.ndarray,
        pose_data: Dict,
        analysis: Dict,
        feedback: Dict
    ) -> np.ndarray:
        """Draw analysis annotations on frame."""
        # Draw pose skeleton
        frame = self.pose_estimator.draw_pose(frame, pose_data)

        # Determine overall color based on score
        score = analysis['score']
        if score >= 9.0:
            score_color = self.colors['good']
        elif score >= 8.0:
            score_color = self.colors['warning']
        else:
            score_color = self.colors['error']

        # Draw header with score
        self._draw_header(frame, analysis, score_color)

        # Draw key corrections
        self._draw_corrections(frame, feedback)

        # Draw injury warnings if any
        if feedback.get('injury_warnings'):
            self._draw_injury_warnings(frame, feedback['injury_warnings'])

        return frame

    def _draw_header(self, frame: np.ndarray, analysis: Dict, color: tuple):
        """Draw header with skill and score."""
        h, w = frame.shape[:2]

        # Semi-transparent overlay for header
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 80), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

        # Draw skill name
        skill = analysis.get('skill_name', analysis.get('skill', 'Unknown'))
        self._draw_text(
            frame,
            f"Skill: {skill.upper()}",
            (20, 30),
            self.colors['neutral'],
            font_scale=0.8,
            thickness=2
        )

        # Draw score
        score = analysis['score']
        quality = analysis['overall_quality']
        self._draw_text(
            frame,
            f"Score: {score:.1f}/10.0 - {quality}",
            (20, 60),
            color,
            font_scale=0.7,
            thickness=2
        )

    def _draw_corrections(self, frame: np.ndarray, feedback: Dict):
        """Draw top corrections on frame."""
        corrections = feedback.get('corrections', [])

        if not corrections:
            return

        h, w = frame.shape[:2]

        # Draw corrections panel on right side
        panel_width = 400
        panel_x = w - panel_width - 10
        panel_y = 100

        # Semi-transparent background
        overlay = frame.copy()
        cv2.rectangle(
            overlay,
            (panel_x - 10, panel_y - 10),
            (w - 10, panel_y + min(len(corrections), 3) * 60 + 20),
            (0, 0, 0),
            -1
        )
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        # Draw title
        self._draw_text(
            frame,
            "KEY CORRECTIONS:",
            (panel_x, panel_y),
            self.colors['warning'],
            font_scale=0.6,
            thickness=2
        )

        # Draw top 3 corrections
        for i, correction in enumerate(corrections[:3]):
            y_pos = panel_y + 40 + (i * 60)

            # Truncate long corrections
            if len(correction) > 60:
                correction = correction[:57] + "..."

            # Determine color based on prefix
            if '🔴' in correction:
                color = self.colors['error']
            elif '🟠' in correction:
                color = (0, 140, 255)  # Orange
            else:
                color = self.colors['warning']

            self._draw_text(
                frame,
                correction,
                (panel_x, y_pos),
                color,
                font_scale=0.45,
                thickness=1
            )

    def _draw_injury_warnings(self, frame: np.ndarray, warnings: List[str]):
        """Draw injury warnings prominently."""
        if not warnings:
            return

        h, w = frame.shape[:2]

        # Draw warning banner at bottom
        banner_height = 60
        overlay = frame.copy()
        cv2.rectangle(
            overlay,
            (0, h - banner_height),
            (w, h),
            (0, 0, 139),  # Dark red
            -1
        )
        cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)

        # Draw warning text
        warning_text = " | ".join(warnings[:2])  # Show max 2 warnings
        if len(warning_text) > 100:
            warning_text = warning_text[:97] + "..."

        self._draw_text(
            frame,
            f"⚠️  {warning_text}",
            (20, h - 30),
            (255, 255, 255),
            font_scale=0.6,
            thickness=2
        )

    def _draw_text(
        self,
        frame: np.ndarray,
        text: str,
        position: tuple,
        color: tuple,
        font_scale: float = 0.6,
        thickness: int = 1
    ):
        """Draw text with shadow for better visibility."""
        font = cv2.FONT_HERSHEY_SIMPLEX

        # Draw shadow
        cv2.putText(
            frame,
            text,
            (position[0] + 2, position[1] + 2),
            font,
            font_scale,
            (0, 0, 0),
            thickness + 1
        )

        # Draw text
        cv2.putText(
            frame,
            text,
            position,
            font,
            font_scale,
            color,
            thickness
        )

    def _compile_results(
        self,
        frame_analyses: List[Dict],
        best_frame: Optional[Dict],
        worst_frame: Optional[Dict],
        total_frames: int,
        fps: int
    ) -> Dict:
        """Compile final analysis results."""
        if not frame_analyses:
            return {
                'analyzed_frames': 0,
                'total_frames': total_frames,
                'average_score': 0.0,
                'best_score': 0.0,
                'worst_score': 0.0,
                'skill_detected': None
            }

        # Calculate statistics
        scores = [a['score'] for a in frame_analyses]
        avg_score = sum(scores) / len(scores)

        # Count errors by type
        all_errors = []
        for analysis in frame_analyses:
            all_errors.extend(analysis.get('errors', []))

        error_counts = {}
        for error in all_errors:
            angle = error.get('angle', 'unknown')
            error_counts[angle] = error_counts.get(angle, 0) + 1

        # Most common skill detected
        skills = [a.get('skill') for a in frame_analyses if a.get('skill')]
        most_common_skill = max(set(skills), key=skills.count) if skills else None

        results = {
            'analyzed_frames': len(frame_analyses),
            'total_frames': total_frames,
            'fps': fps,
            'average_score': round(avg_score, 2),
            'best_score': round(best_frame['analysis']['score'], 2) if best_frame else 0.0,
            'worst_score': round(worst_frame['analysis']['score'], 2) if worst_frame else 10.0,
            'best_frame_number': best_frame['frame_number'] if best_frame else None,
            'worst_frame_number': worst_frame['frame_number'] if worst_frame else None,
            'best_timestamp': best_frame['timestamp'] if best_frame else None,
            'worst_timestamp': worst_frame['timestamp'] if worst_frame else None,
            'skill_detected': most_common_skill,
            'common_errors': error_counts,
            'frame_analyses': frame_analyses,
            'best_frame_analysis': best_frame['analysis'] if best_frame else None,
            'worst_frame_analysis': worst_frame['analysis'] if worst_frame else None
        }

        return results
