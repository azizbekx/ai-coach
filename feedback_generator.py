"""
Generates actionable coaching feedback from analysis results.
"""

from typing import Dict, List
from config import COLORS


class FeedbackGenerator:
    """Generates human-readable coaching feedback from technical analysis."""

    def __init__(self):
        """Initialize feedback generator."""
        self.colors = COLORS

    def generate_feedback(self, analysis: Dict) -> Dict:
        """
        Generate comprehensive coaching feedback.

        Args:
            analysis: Analysis results from GymnasticsAnalyzer

        Returns:
            Dictionary with formatted feedback messages
        """
        if not analysis or analysis['score'] == 0.0:
            return {
                'summary': 'Unable to analyze pose - ensure athlete is fully visible',
                'corrections': [],
                'praise': [],
                'injury_warnings': [],
                'overall_assessment': 'No analysis available'
            }

        feedback = {
            'skill': analysis.get('skill_name', analysis.get('skill', 'Unknown')),
            'score': analysis['score'],
            'quality': analysis['overall_quality'],
            'summary': self._generate_summary(analysis),
            'corrections': self._generate_corrections(analysis),
            'praise': self._generate_praise(analysis),
            'injury_warnings': self._generate_injury_warnings(analysis),
            'coaching_tips': self._generate_coaching_tips(analysis),
            'overall_assessment': self._generate_overall_assessment(analysis)
        }

        return feedback

    def _generate_summary(self, analysis: Dict) -> str:
        """Generate one-line summary of performance."""
        skill = analysis.get('skill_name', analysis.get('skill', 'skill'))
        score = analysis['score']
        quality = analysis['overall_quality']

        summary = f"{skill.title()}: {score}/10.0 - {quality}"

        if analysis.get('total_deduction', 0) > 0:
            summary += f" (deductions: -{analysis['total_deduction']})"

        return summary

    def _generate_corrections(self, analysis: Dict) -> List[str]:
        """Generate specific correction instructions."""
        corrections = []

        # Process errors by severity
        errors = sorted(
            analysis.get('errors', []),
            key=lambda x: self._severity_priority(x.get('severity', 'minor')),
            reverse=True
        )

        for error in errors:
            correction = self._format_correction(error)
            if correction:
                corrections.append(correction)

        # Add warnings if no major errors
        if len(errors) < 3:
            for warning in analysis.get('warnings', [])[:2]:
                correction = self._format_warning(warning)
                if correction:
                    corrections.append(correction)

        return corrections

    def _format_correction(self, error: Dict) -> str:
        """Format a single correction message."""
        angle = error.get('angle', 'position')
        description = error.get('description', '')
        measured = error.get('measured')
        ideal = error.get('ideal')
        severity = error.get('severity', 'minor')

        # Severity prefix
        prefix = {
            'severe': '🔴 CRITICAL',
            'major': '🟠 MAJOR',
            'moderate': '🟡 FIX',
            'minor': '⚪ IMPROVE'
        }.get(severity, '⚪')

        if measured is not None and ideal is not None:
            deviation = abs(measured - ideal)
            direction = 'more' if measured < ideal else 'less'

            return (f"{prefix}: {description}. "
                   f"Current: {measured:.1f}°, Target: {ideal:.1f}° "
                   f"(adjust {direction} by {deviation:.1f}°)")
        else:
            return f"{prefix}: {description}"

    def _format_warning(self, warning: Dict) -> str:
        """Format a warning message."""
        description = warning.get('description', '')
        measured = warning.get('measured')
        ideal = warning.get('ideal')

        if measured is not None and ideal is not None:
            return f"⚪ IMPROVE: {description}. Current: {measured:.1f}°, Target: {ideal:.1f}°"
        else:
            return f"⚪ NOTE: {description}"

    def _generate_praise(self, analysis: Dict) -> List[str]:
        """Generate positive feedback for good form elements."""
        praise = []

        score = analysis['score']

        if score >= 9.5:
            praise.append("🌟 Outstanding technique!")
            praise.append("✨ Excellent body control and precision")

        elif score >= 9.0:
            praise.append("👏 Great execution!")
            praise.append("💪 Strong fundamentals")

        elif score >= 8.5:
            praise.append("✓ Good form overall")

        # Check for specific good elements
        detected_angles = analysis.get('detected_angles', {})

        # Check for good toe point
        left_ankle = detected_angles.get('left_ankle')
        right_ankle = detected_angles.get('right_ankle')
        if left_ankle and left_ankle > 165:
            praise.append("✓ Excellent toe point on left foot")
        if right_ankle and right_ankle > 165:
            praise.append("✓ Excellent toe point on right foot")

        # Check for straight arms
        left_elbow = detected_angles.get('left_elbow')
        right_elbow = detected_angles.get('right_elbow')
        if left_elbow and left_elbow > 175:
            praise.append("✓ Perfect arm extension (left)")
        if right_elbow and right_elbow > 175:
            praise.append("✓ Perfect arm extension (right)")

        # Check for good body alignment
        torso = detected_angles.get('torso_vertical')
        if torso and torso > 175:
            praise.append("✓ Excellent body alignment")

        return praise

    def _generate_injury_warnings(self, analysis: Dict) -> List[str]:
        """Generate injury risk warnings."""
        warnings = []

        injury_risks = analysis.get('injury_risks', [])

        for risk in injury_risks:
            severity = risk.get('severity', 'medium')
            description = risk.get('description', '')
            recommendation = risk.get('recommendation', '')

            if severity == 'high':
                warnings.append(f"⚠️ HIGH RISK: {description}")
                warnings.append(f"   → {recommendation}")
            elif severity == 'medium':
                warnings.append(f"⚠️ CAUTION: {description}")
                warnings.append(f"   → {recommendation}")

        return warnings

    def _generate_coaching_tips(self, analysis: Dict) -> List[str]:
        """Generate actionable coaching tips based on common errors."""
        tips = []

        errors = analysis.get('errors', [])

        # Group errors by type and provide targeted tips
        error_types = set(error.get('angle', '') for error in errors)

        if 'left_hip' in error_types or 'right_hip' in error_types:
            tips.append("💡 Focus on hip engagement: Squeeze glutes and engage core for better hip control")

        if 'left_knee' in error_types or 'right_knee' in error_types:
            tips.append("💡 Knee control: Focus on quadriceps engagement to maintain leg extension")

        if 'left_shoulder' in error_types or 'right_shoulder' in error_types:
            tips.append("💡 Shoulder positioning: Pull shoulders down and back, engage lats")

        if 'torso_vertical' in error_types or 'body_vertical' in error_types:
            tips.append("💡 Body alignment: Engage core and visualize a straight line from head to toe")

        if 'left_toes' in error_types or 'right_toes' in error_types:
            tips.append("💡 Toe point: Push through the ankle, point toes actively")

        # Add skill-specific tips
        skill = analysis.get('skill', '')

        if skill == 'handstand':
            tips.append("💡 Handstand tip: Focus weight over fingertips, push through shoulders")
        elif skill == 'bridge':
            tips.append("💡 Bridge tip: Push hips up toward ceiling, keep weight evenly distributed")
        elif skill == 'split':
            tips.append("💡 Split tip: Keep hips square, gradually deepen stretch over time")

        return tips[:3]  # Return top 3 tips

    def _generate_overall_assessment(self, analysis: Dict) -> str:
        """Generate overall coaching assessment."""
        score = analysis['score']
        quality = analysis['overall_quality']
        skill = analysis.get('skill_name', analysis.get('skill', 'skill'))

        error_count = len(analysis.get('errors', []))
        warning_count = len(analysis.get('warnings', []))
        injury_risk_count = len(analysis.get('injury_risks', []))

        assessment = f"Overall: {quality} execution of {skill}. "

        if score >= 9.5:
            assessment += "Excellent work! This is competition-ready form. Focus on consistency."
        elif score >= 9.0:
            assessment += "Strong performance with minor areas for improvement. Keep refining."
        elif score >= 8.5:
            assessment += "Good foundation. Address the corrections above to reach elite level."
        elif score >= 8.0:
            assessment += "Fair execution. Focus on the key technical elements highlighted."
        else:
            assessment += "Significant technical work needed. Address form errors systematically."

        if injury_risk_count > 0:
            assessment += f" ⚠️ {injury_risk_count} injury risk(s) detected - prioritize safety."

        if error_count > 0:
            assessment += f" Work on {error_count} correction(s) identified."

        return assessment

    def _severity_priority(self, severity: str) -> int:
        """Return priority number for sorting by severity."""
        priority_map = {
            'severe': 4,
            'major': 3,
            'moderate': 2,
            'minor': 1
        }
        return priority_map.get(severity, 0)

    def format_for_display(self, feedback: Dict) -> str:
        """
        Format feedback as readable text for display.

        Args:
            feedback: Feedback dictionary

        Returns:
            Formatted string for display
        """
        lines = []

        lines.append("=" * 60)
        lines.append("AI GYMNASTICS COACH - TECHNIQUE ANALYSIS")
        lines.append("=" * 60)
        lines.append("")

        # Summary
        lines.append(f"SKILL: {feedback.get('skill', 'Unknown')}")
        lines.append(f"SCORE: {feedback.get('score', 0)}/10.0")
        lines.append(f"QUALITY: {feedback.get('quality', 'N/A')}")
        lines.append("")

        # Praise
        praise = feedback.get('praise', [])
        if praise:
            lines.append("✓ STRENGTHS:")
            for item in praise:
                lines.append(f"  {item}")
            lines.append("")

        # Injury warnings (highest priority)
        injury_warnings = feedback.get('injury_warnings', [])
        if injury_warnings:
            lines.append("⚠️  INJURY RISKS:")
            for warning in injury_warnings:
                lines.append(f"  {warning}")
            lines.append("")

        # Corrections
        corrections = feedback.get('corrections', [])
        if corrections:
            lines.append("🎯 CORRECTIONS NEEDED:")
            for i, correction in enumerate(corrections, 1):
                lines.append(f"  {i}. {correction}")
            lines.append("")

        # Coaching tips
        tips = feedback.get('coaching_tips', [])
        if tips:
            lines.append("💡 COACHING TIPS:")
            for tip in tips:
                lines.append(f"  {tip}")
            lines.append("")

        # Overall assessment
        lines.append("📊 OVERALL ASSESSMENT:")
        lines.append(f"  {feedback.get('overall_assessment', 'No assessment available')}")
        lines.append("")

        lines.append("=" * 60)

        return "\n".join(lines)
