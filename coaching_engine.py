"""
Coaching Engine - Manages step-by-step skill teaching with AI guidance.
"""

from typing import Dict, List, Optional
import numpy as np
from config import SKILL_LEARNING_STEPS


class CoachingEngine:
    """Manages progressive skill teaching with step-by-step guidance."""

    def __init__(self):
        """Initialize coaching engine with skill learning templates."""
        self.skill_steps = SKILL_LEARNING_STEPS
        self.active_sessions = {}  # Track user coaching sessions

    def start_coaching_session(self, skill: str, session_id: str = "default") -> Dict:
        """
        Start a new coaching session for a skill.

        Args:
            skill: Name of the skill to learn
            session_id: Unique session identifier

        Returns:
            Dictionary with session info and first step
        """
        if skill not in self.skill_steps:
            return {
                'success': False,
                'error': f'Skill "{skill}" not available for coaching'
            }

        steps = self.skill_steps[skill]['steps']

        # Initialize session
        self.active_sessions[session_id] = {
            'skill': skill,
            'current_step': 0,
            'completed_steps': [],
            'attempts': 0,
            'total_steps': len(steps)
        }

        return {
            'success': True,
            'skill': skill,
            'skill_name': self.skill_steps[skill]['name'],
            'description': self.skill_steps[skill]['description'],
            'total_steps': len(steps),
            'current_step': 0,
            'step_info': steps[0],
            'welcome_message': self._get_welcome_message(skill)
        }

    def get_current_step(self, session_id: str = "default") -> Optional[Dict]:
        """Get current step information for a session."""
        session = self.active_sessions.get(session_id)
        if not session:
            return None

        skill = session['skill']
        step_index = session['current_step']
        steps = self.skill_steps[skill]['steps']

        if step_index >= len(steps):
            return {
                'completed': True,
                'message': 'Congratulations! You have completed all steps!'
            }

        return {
            'step_number': step_index + 1,
            'total_steps': len(steps),
            'step_info': steps[step_index],
            'skill': skill
        }

    def advance_to_next_step(self, session_id: str = "default") -> Dict:
        """Move to the next step in the progression."""
        session = self.active_sessions.get(session_id)
        if not session:
            return {'success': False, 'error': 'No active session'}

        current_step = session['current_step']
        session['completed_steps'].append(current_step)
        session['current_step'] += 1

        skill = session['skill']
        steps = self.skill_steps[skill]['steps']

        if session['current_step'] >= len(steps):
            return {
                'success': True,
                'completed': True,
                'message': f"🎉 Congratulations! You've mastered the {self.skill_steps[skill]['name']}!",
                'next_skill_suggestions': self._get_next_skill_suggestions(skill)
            }

        return {
            'success': True,
            'completed': False,
            'step_number': session['current_step'] + 1,
            'total_steps': len(steps),
            'step_info': steps[session['current_step']],
            'encouragement': self._get_encouragement(session['current_step'], len(steps))
        }

    def evaluate_step_completion(
        self,
        angles: Dict[str, float],
        session_id: str = "default"
    ) -> Dict:
        """
        Evaluate if current step requirements are met.

        Args:
            angles: Detected body angles
            session_id: Session identifier

        Returns:
            Evaluation results with completion status
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return {'success': False, 'error': 'No active session'}

        skill = session['skill']
        step_index = session['current_step']
        steps = self.skill_steps[skill]['steps']

        if step_index >= len(steps):
            return {'completed': True}

        step = steps[step_index]
        session['attempts'] += 1

        # Check if step requirements are met
        requirements = step.get('requirements', {})
        checks = []
        all_passed = True

        for angle_name, criteria in requirements.items():
            measured = self._get_angle_value(angle_name, angles)

            if measured is None:
                all_passed = False
                checks.append({
                    'requirement': angle_name,
                    'status': 'not_detected',
                    'message': f"Cannot detect {angle_name.replace('_', ' ')}"
                })
                continue

            target = criteria.get('target')
            tolerance = criteria.get('tolerance', 15)
            min_val = criteria.get('min')
            max_val = criteria.get('max')

            passed = False
            message = ""

            if target is not None:
                deviation = abs(measured - target)
                passed = deviation <= tolerance
                if passed:
                    message = f"✓ {criteria['description']}: Perfect! ({measured:.1f}°)"
                else:
                    direction = "more" if measured < target else "less"
                    message = f"✗ {criteria['description']}: Need {direction} ({measured:.1f}° vs {target}°)"

            elif min_val is not None and max_val is not None:
                passed = min_val <= measured <= max_val
                if passed:
                    message = f"✓ {criteria['description']}: Good! ({measured:.1f}°)"
                else:
                    message = f"✗ {criteria['description']}: Adjust position ({measured:.1f}°)"

            checks.append({
                'requirement': angle_name,
                'status': 'passed' if passed else 'failed',
                'measured': measured,
                'target': target,
                'message': message
            })

            if not passed:
                all_passed = False

        return {
            'success': True,
            'step_completed': all_passed,
            'checks': checks,
            'attempts': session['attempts'],
            'feedback': self._generate_step_feedback(checks, all_passed, step)
        }

    def _get_angle_value(self, angle_name: str, angles: Dict[str, float]) -> Optional[float]:
        """Map requirement angle names to measured angles."""
        # Direct match
        if angle_name in angles:
            return angles[angle_name]

        # Handle average cases
        if angle_name == 'shoulder_angle':
            left = angles.get('left_shoulder')
            right = angles.get('right_shoulder')
            if left and right:
                return (left + right) / 2
            return left or right

        if angle_name == 'hip_angle':
            left = angles.get('left_hip')
            right = angles.get('right_hip')
            if left and right:
                return (left + right) / 2
            return left or right

        if angle_name == 'knee_angle':
            left = angles.get('left_knee')
            right = angles.get('right_knee')
            if left and right:
                return (left + right) / 2
            return left or right

        return angles.get(angle_name)

    def _generate_step_feedback(self, checks: List[Dict], completed: bool, step: Dict) -> str:
        """Generate encouraging feedback for step attempt."""
        if completed:
            return f"✅ Excellent! {step['instruction']} - Moving to next step!"

        # Find what needs work
        failed = [c for c in checks if c['status'] == 'failed']

        if len(failed) == 1:
            return f"💡 Almost there! Focus on: {failed[0]['message']}"
        elif len(failed) <= 3:
            issues = ", ".join([c['requirement'].replace('_', ' ') for c in failed])
            return f"💪 Keep trying! Work on: {issues}"
        else:
            return f"🎯 {step['coaching_cue']} - Take your time and focus on form!"

    def _get_welcome_message(self, skill: str) -> str:
        """Generate welcome message for a skill."""
        skill_info = self.skill_steps[skill]
        return (
            f"Welcome to {skill_info['name']} training! "
            f"I'll guide you through {len(skill_info['steps'])} progressive steps. "
            f"Take your time and focus on proper form. Let's begin!"
        )

    def _get_encouragement(self, step_number: int, total_steps: int) -> str:
        """Generate encouraging message based on progress."""
        progress = (step_number / total_steps) * 100

        if progress >= 75:
            return "🌟 Amazing progress! You're almost there!"
        elif progress >= 50:
            return "💪 Great work! You're halfway through!"
        elif progress >= 25:
            return "👏 Excellent! Keep up the good work!"
        else:
            return "✨ Good start! Let's continue!"

    def _get_next_skill_suggestions(self, completed_skill: str) -> List[str]:
        """Suggest next skills to learn based on progression."""
        progression = {
            'bridge': ['split', 'handstand'],
            'split': ['pike', 'bridge'],
            'pike': ['tuck', 'handstand'],
            'tuck': ['pike', 'handstand'],
            'handstand': []  # Advanced skill
        }

        return progression.get(completed_skill, [])

    def get_gemini_coaching_prompt(
        self,
        skill: str,
        step_info: Dict,
        angles: Dict[str, float],
        evaluation: Dict
    ) -> str:
        """
        Generate a prompt for Gemini to provide natural coaching feedback.

        Args:
            skill: Current skill being learned
            step_info: Current step information
            angles: Detected body angles
            evaluation: Step evaluation results

        Returns:
            Prompt string for Gemini
        """
        step_completed = evaluation.get('step_completed', False)
        checks = evaluation.get('checks', [])

        # Build context
        failed_checks = [c for c in checks if c['status'] == 'failed']
        passed_checks = [c for c in checks if c['status'] == 'passed']

        prompt = f"""You are an encouraging gymnastics coach teaching a student the {skill}.

Current Step: {step_info['name']}
Instruction: {step_info['instruction']}
Coaching Cue: {step_info['coaching_cue']}

Current Performance:
"""

        if passed_checks:
            prompt += "\n✓ GOOD:\n"
            for check in passed_checks:
                prompt += f"  - {check['message']}\n"

        if failed_checks:
            prompt += "\n✗ NEEDS WORK:\n"
            for check in failed_checks:
                prompt += f"  - {check['message']}\n"

        if step_completed:
            prompt += """
The student has successfully completed this step!

Please provide:
1. Enthusiastic praise (1 sentence)
2. What they did well (1-2 specific points)
3. Brief preview of the next step (1 sentence)

Keep it conversational, encouraging, and brief (3-4 sentences total).
"""
        else:
            prompt += """
The student hasn't completed this step yet.

Please provide:
1. Brief encouragement (1 sentence)
2. ONE specific actionable correction to focus on RIGHT NOW
3. A simple coaching cue to help them (1 short phrase)

Keep it brief and actionable (2-3 sentences total). Be supportive and motivating!
"""

        return prompt

    def format_coaching_response(
        self,
        gemini_response: str,
        step_completed: bool,
        step_number: int,
        total_steps: int
    ) -> Dict:
        """Format Gemini response for frontend display and audio."""
        return {
            'message': gemini_response,
            'step_completed': step_completed,
            'progress': {
                'current': step_number,
                'total': total_steps,
                'percentage': int((step_number / total_steps) * 100)
            },
            'audio_text': gemini_response  # Clean text for TTS
        }
