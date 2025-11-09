#!/usr/bin/env python3
"""
AI Gymnastics Coach - Main Application

Process gymnastics videos and provide real-time technique analysis and feedback.
"""

import argparse
import sys
import os
from pathlib import Path

import cv2
import numpy as np

# Suppress macOS-specific NS warnings for camera/MediaPipe
os.environ['OPENCV_AVFOUNDATION_SKIP_AUTH'] = '1'

from video_processor import VideoProcessor
from feedback_generator import FeedbackGenerator
from gymnastics_analyzer import GymnasticsAnalyzer
from pose_estimator import PoseEstimator


def process_video_file(video_path: str, output_path: str = None, show_preview: bool = False):
    """
    Process a video file and generate analysis.

    Args:
        video_path: Path to input video
        output_path: Optional path for annotated output video
        show_preview: Whether to show live preview
    """
    processor = VideoProcessor()

    print("\n" + "=" * 60)
    print("AI GYMNASTICS COACH - VIDEO ANALYSIS")
    print("=" * 60)

    # Auto-generate output path if not provided
    if output_path is None and not show_preview:
        video_path_obj = Path(video_path)
        output_path = str(
            video_path_obj.parent / f"{video_path_obj.stem}_analyzed{video_path_obj.suffix}"
        )

    # Progress callback
    def progress_callback(progress, frame, total):
        if frame % 30 == 0:
            print(f"Progress: {progress:.1f}% ({frame}/{total} frames)", end='\r')

    # Process video
    results = processor.process_video(
        video_path=video_path,
        output_path=output_path,
        show_preview=show_preview,
        analyze_every_n_frames=1,  # Analyze every frame for best results
        progress_callback=progress_callback
    )

    # Display detailed results
    print("\n")
    print_detailed_results(results)

    # Generate feedback for best and worst frames
    if results['best_frame_analysis']:
        print("\n" + "=" * 60)
        print("BEST PERFORMANCE FRAME ANALYSIS")
        print(f"Frame: {results['best_frame_number']} at {results['best_timestamp']:.2f}s")
        print("=" * 60)

        feedback_gen = FeedbackGenerator()
        best_feedback = feedback_gen.generate_feedback(results['best_frame_analysis'])
        print(feedback_gen.format_for_display(best_feedback))

    if results['worst_frame_analysis']:
        print("\n" + "=" * 60)
        print("FRAME NEEDING MOST IMPROVEMENT")
        print(f"Frame: {results['worst_frame_number']} at {results['worst_timestamp']:.2f}s")
        print("=" * 60)

        feedback_gen = FeedbackGenerator()
        worst_feedback = feedback_gen.generate_feedback(results['worst_frame_analysis'])
        print(feedback_gen.format_for_display(worst_feedback))


def process_webcam():
    """Process webcam feed in real-time."""
    processor = VideoProcessor()

    print("\n" + "=" * 60)
    print("AI GYMNASTICS COACH - LIVE CAMERA MODE")
    print("=" * 60)
    print("Press 'q' to quit, 's' to save screenshot")
    print("=" * 60 + "\n")

    cap = cv2.VideoCapture(0)

    # Set camera properties to avoid macOS NS warnings
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print("Error: Could not open webcam")
        return

    screenshot_count = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Process frame
            result = processor.process_frame(frame, draw_annotations=True)

            # Display
            cv2.imshow('AI Gymnastics Coach - Live Feed', result['frame'])

            # Handle keys
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                break
            elif key == ord('s'):
                # Save screenshot
                screenshot_path = f"screenshot_{screenshot_count}.jpg"
                cv2.imwrite(screenshot_path, result['frame'])
                print(f"Screenshot saved: {screenshot_path}")
                screenshot_count += 1

                # Print feedback
                if result['pose_detected']:
                    feedback_gen = FeedbackGenerator()
                    feedback = feedback_gen.generate_feedback(result['analysis'])
                    print("\n" + feedback_gen.format_for_display(feedback))

    finally:
        cap.release()
        cv2.destroyAllWindows()


def analyze_image(image_path: str, output_path: str = None):
    """
    Analyze a single image.

    Args:
        image_path: Path to input image
        output_path: Optional path for annotated output image
    """
    processor = VideoProcessor()

    print("\n" + "=" * 60)
    print("AI GYMNASTICS COACH - IMAGE ANALYSIS")
    print("=" * 60)

    # Read image
    frame = cv2.imread(image_path)
    if frame is None:
        print(f"Error: Could not read image: {image_path}")
        return

    # Process image
    result = processor.process_frame(frame, draw_annotations=True)

    if not result['pose_detected']:
        print("Error: No pose detected in image")
        return

    # Save annotated image
    if output_path is None:
        image_path_obj = Path(image_path)
        output_path = str(
            image_path_obj.parent / f"{image_path_obj.stem}_analyzed{image_path_obj.suffix}"
        )

    cv2.imwrite(output_path, result['frame'])
    print(f"\nAnnotated image saved: {output_path}")

    # Generate and display feedback
    feedback_gen = FeedbackGenerator()
    feedback = feedback_gen.generate_feedback(result['analysis'])
    print("\n" + feedback_gen.format_for_display(feedback))


def print_detailed_results(results: dict):
    """Print detailed analysis results."""
    print("\n" + "=" * 60)
    print("DETAILED ANALYSIS SUMMARY")
    print("=" * 60)

    print(f"\nTotal Frames: {results['total_frames']}")
    print(f"Analyzed Frames: {results['analyzed_frames']}")
    print(f"FPS: {results['fps']}")

    print(f"\n📊 SCORES:")
    print(f"  Average: {results['average_score']:.2f}/10.0")
    print(f"  Best: {results['best_score']:.2f} (frame {results['best_frame_number']})")
    print(f"  Worst: {results['worst_score']:.2f} (frame {results['worst_frame_number']})")

    if results['skill_detected']:
        print(f"\n🤸 DETECTED SKILL: {results['skill_detected'].upper()}")

    if results['common_errors']:
        print(f"\n⚠️  MOST COMMON ERRORS:")
        sorted_errors = sorted(
            results['common_errors'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        for error, count in sorted_errors[:5]:
            print(f"  - {error}: {count} occurrences")


def demo_mode():
    """Run demo with sample analysis."""
    print("\n" + "=" * 60)
    print("AI GYMNASTICS COACH - DEMO MODE")
    print("=" * 60)
    print("\nThis demo shows the AI coach analyzing a gymnastics pose.")
    print("\nFor full functionality, provide:")
    print("  - A video file: python coach.py --video <path>")
    print("  - A webcam feed: python coach.py --webcam")
    print("  - An image: python coach.py --image <path>")
    print("\n" + "=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='AI Gymnastics Coach - Technique Analysis System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a video file
  python coach.py --video gymnastics.mp4

  # Analyze with live preview
  python coach.py --video gymnastics.mp4 --preview

  # Specify output location
  python coach.py --video input.mp4 --output analyzed.mp4

  # Use webcam for live analysis
  python coach.py --webcam

  # Analyze a single image
  python coach.py --image pose.jpg
        """
    )

    parser.add_argument(
        '--video',
        type=str,
        help='Path to input video file'
    )

    parser.add_argument(
        '--output',
        type=str,
        help='Path to output video/image file (auto-generated if not specified)'
    )

    parser.add_argument(
        '--preview',
        action='store_true',
        help='Show live preview while processing video'
    )

    parser.add_argument(
        '--webcam',
        action='store_true',
        help='Use webcam for live analysis'
    )

    parser.add_argument(
        '--image',
        type=str,
        help='Path to input image file'
    )

    parser.add_argument(
        '--demo',
        action='store_true',
        help='Run demo mode'
    )

    args = parser.parse_args()

    # Validate inputs
    if args.video:
        if not Path(args.video).exists():
            print(f"Error: Video file not found: {args.video}")
            sys.exit(1)
        process_video_file(args.video, args.output, args.preview)

    elif args.image:
        if not Path(args.image).exists():
            print(f"Error: Image file not found: {args.image}")
            sys.exit(1)
        analyze_image(args.image, args.output)

    elif args.webcam:
        process_webcam()

    elif args.demo:
        demo_mode()

    else:
        # No arguments - show help
        parser.print_help()
        print("\n" + "=" * 60)
        print("TIP: Start with --demo or --webcam to see the system in action!")
        print("=" * 60)


if __name__ == '__main__':
    main()
