# Quick Start Guide - AI Gymnastics Coach

Get up and running in 5 minutes!

## Installation

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Test installation
python test_installation.py
```

## First Run - Webcam Demo

The fastest way to see the AI coach in action:

```bash
python coach.py --webcam
```

- Point your webcam at someone doing a gymnastics pose
- Press 's' to capture and analyze a frame
- Press 'q' to quit

## Analyze a Video

If you have a gymnastics video:

```bash
python coach.py --video your_video.mp4
```

This will:
- Analyze the entire video
- Create an annotated output video
- Print detailed feedback

## What You'll See

The system provides:

### 1. **Real-time Visual Overlay**
- Skeleton tracking on the athlete
- Score display (0-10 scale)
- Skill detection
- Key corrections highlighted

### 2. **Detailed Feedback**
```
SKILL: Handstand
SCORE: 8.7/10.0
QUALITY: Good

✓ STRENGTHS:
  ✓ Excellent toe point
  ✓ Perfect arm extension

🎯 CORRECTIONS NEEDED:
  1. Right shoulder should be fully extended (adjust 17.7°)
  2. Hips should be fully extended (adjust 11.5°)

💡 COACHING TIPS:
  💡 Pull shoulders down and back, engage lats
  💡 Focus weight over fingertips
```

### 3. **Injury Warnings**
```
⚠️ HIGH RISK: Left knee hyperextension detected
   → Engage quadriceps, avoid locking knee
```

## Sample Commands

```bash
# Analyze with live preview window
python coach.py --video routine.mp4 --preview

# Analyze a single image
python coach.py --image handstand.jpg

# Specify output location
python coach.py --video input.mp4 --output analyzed.mp4

# Get help
python coach.py --help
```

## Getting Sample Videos

### Option 1: Use Your Phone
- Record a gymnastics skill (handstand, split, bridge)
- Transfer video to your computer
- Analyze it!

### Option 2: YouTube
1. Find a gymnastics tutorial video
2. Use a YouTube downloader
3. Analyze the video

### Option 3: Public Datasets
- FineGYM: https://sdolivia.github.io/FineGym/
- Contains thousands of gymnastics routines

## Supported Skills

The AI coach currently recognizes:

- **Handstand**: Arms overhead, body vertical
- **Split**: Legs extended in opposite directions
- **Bridge**: Back bend with hands and feet on ground
- **Pike**: Bent at hips, legs straight
- **Tuck**: Knees to chest position

More skills can be easily added to `config.py`!

## Tips for Best Results

1. **Good Lighting**: Ensure the athlete is well-lit
2. **Full Body Visible**: Camera should capture entire body
3. **Clear Background**: Avoid cluttered backgrounds
4. **Side or Front Angle**: Best camera angles for analysis
5. **Steady Camera**: Use a tripod if possible

## Troubleshooting

**"No pose detected"**
- Ensure full body is visible in frame
- Check lighting conditions
- Move camera further back

**"Could not open webcam"**
- Check webcam permissions
- Ensure webcam is connected
- Try another camera index (edit code)

**Slow processing**
- Reduce video resolution
- Analyze every N frames instead of all
- Use a GPU if available

## What's Next?

- Read the full [README.md](README.md) for detailed documentation
- Explore `config.py` to customize skill templates
- Try different gymnastics skills
- Track improvement over time

## Need Help?

- Check the main README.md for full documentation
- Review example output in the demo
- Examine the code - it's well-commented!

---

**Ready to win some medals? Let's train! 🥇**
