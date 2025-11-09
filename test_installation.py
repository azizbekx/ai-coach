#!/usr/bin/env python3
"""
Test script to validate AI Gymnastics Coach installation.
"""

import sys


def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")

    try:
        import cv2
        print("✓ OpenCV imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import OpenCV: {e}")
        return False

    try:
        import mediapipe
        print("✓ MediaPipe imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import MediaPipe: {e}")
        return False

    try:
        import numpy
        print("✓ NumPy imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import NumPy: {e}")
        return False

    try:
        import scipy
        print("✓ SciPy imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import SciPy: {e}")
        return False

    try:
        import matplotlib
        print("✓ Matplotlib imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import Matplotlib: {e}")
        return False

    return True


def test_modules():
    """Test that project modules can be imported."""
    print("\nTesting project modules...")

    try:
        from pose_estimator import PoseEstimator
        print("✓ PoseEstimator imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import PoseEstimator: {e}")
        return False

    try:
        from gymnastics_analyzer import GymnasticsAnalyzer
        print("✓ GymnasticsAnalyzer imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import GymnasticsAnalyzer: {e}")
        return False

    try:
        from feedback_generator import FeedbackGenerator
        print("✓ FeedbackGenerator imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import FeedbackGenerator: {e}")
        return False

    try:
        from video_processor import VideoProcessor
        print("✓ VideoProcessor imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import VideoProcessor: {e}")
        return False

    return True


def test_initialization():
    """Test that main components can be initialized."""
    print("\nTesting component initialization...")

    try:
        from pose_estimator import PoseEstimator
        estimator = PoseEstimator()
        print("✓ PoseEstimator initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize PoseEstimator: {e}")
        return False

    try:
        from gymnastics_analyzer import GymnasticsAnalyzer
        analyzer = GymnasticsAnalyzer()
        print("✓ GymnasticsAnalyzer initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize GymnasticsAnalyzer: {e}")
        return False

    try:
        from feedback_generator import FeedbackGenerator
        generator = FeedbackGenerator()
        print("✓ FeedbackGenerator initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize FeedbackGenerator: {e}")
        return False

    try:
        from video_processor import VideoProcessor
        processor = VideoProcessor()
        print("✓ VideoProcessor initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize VideoProcessor: {e}")
        return False

    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("AI GYMNASTICS COACH - INSTALLATION TEST")
    print("=" * 60)
    print()

    # Test imports
    if not test_imports():
        print("\n✗ Import test failed!")
        print("Please run: pip install -r requirements.txt")
        sys.exit(1)

    # Test modules
    if not test_modules():
        print("\n✗ Module import test failed!")
        print("Please ensure all project files are present.")
        sys.exit(1)

    # Test initialization
    if not test_initialization():
        print("\n✗ Initialization test failed!")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED!")
    print("=" * 60)
    print("\nYour installation is working correctly!")
    print("\nNext steps:")
    print("  1. Test with webcam: python coach.py --webcam")
    print("  2. Analyze a video: python coach.py --video <path>")
    print("  3. Read the README.md for more information")
    print()


if __name__ == '__main__':
    main()
