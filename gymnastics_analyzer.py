"""
Gymnastics form analysis engine - evaluates technique against ideal templates.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from config import SKILL_TEMPLATES, GENERAL_FORM, INJURY_RISK_THRESHOLDS, DEDUCTION_RANGES, DEDUCTION_VALUES


class GymnasticsAnalyzer:
    """Analyzes gymnastics form and provides scoring based on technique."""

    def __init__(self):
        """Initialize the analyzer with skill templates."""
        self.skill_templates = SKILL_TEMPLATES
        self.general_form = GENERAL_FORM
        self.injury_thresholds = INJURY_RISK_THRESHOLDS

    def detect_skill(self, angles: Dict[str, float]) -> Optional[str]:
        """
        Detect which gymnastics skill is being performed based on body angles.

        Args:
            angles: Dictionary of measured body angles

        Returns:
            Detected skill name or None
        """
        # Simple heuristic-based skill detection
        # In production, this would use ML models

        if not angles:
            return None

        # Handstand detection: arms overhead, body vertical
        if ('left_shoulder' in angles and 'right_shoulder' in angles and
            'torso_vertical' in angles):
            avg_shoulder = (angles.get('left_shoulder', 0) + angles.get('right_shoulder', 0)) / 2
            if avg_shoulder > 160 and angles.get('torso_vertical', 0) > 160:
                return 'handstand'

        # Pike detection: tight hip angle, straight knees
        if 'left_hip' in angles and 'left_knee' in angles:
            if angles['left_hip'] < 90 and angles['left_knee'] > 160:
                return 'pike'

        # Tuck detection: bent knees and hips
        if 'left_hip' in angles and 'left_knee' in angles:
            if angles['left_hip'] < 90 and angles['left_knee'] < 90:
                return 'tuck'

        # Bridge detection: hips elevated, shoulders extended
        if ('left_shoulder' in angles and 'left_knee' in angles):
            avg_shoulder = (angles.get('left_shoulder', 0) + angles.get('right_shoulder', 0)) / 2
            avg_knee = (angles.get('left_knee', 0) + angles.get('right_knee', 0)) / 2
            if avg_shoulder > 150 and 70 < avg_knee < 110:
                return 'bridge'

        # Split detection: one leg forward, one back, both extended
        if ('left_knee' in angles and 'right_knee' in angles and
            'left_hip' in angles and 'right_hip' in angles):
            if (angles['left_knee'] > 160 and angles['right_knee'] > 160):
                hip_diff = abs(angles['left_hip'] - angles['right_hip'])
                if hip_diff > 60:  # Significant difference suggests split
                    return 'split'

        return 'general'  # Default to general form analysis

    def analyze_form(self, angles: Dict[str, float], skill: Optional[str] = None) -> Dict:
        """
        Analyze form quality against ideal templates.

        Args:
            angles: Measured body angles
            skill: Optional specific skill to analyze (auto-detected if None)

        Returns:
            Analysis results with scores and feedback
        """
        if not angles:
            return {
                'skill': None,
                'score': 0.0,
                'deductions': [],
                'errors': [],
                'warnings': [],
                'overall_quality': 'Unable to detect pose'
            }

        # Auto-detect skill if not provided
        if skill is None:
            skill = self.detect_skill(angles)

        if skill is None or skill not in self.skill_templates:
            skill = 'general'

        results = {
            'skill': skill,
            'detected_angles': angles,
            'deductions': [],
            'errors': [],
            'warnings': [],
            'injury_risks': []
        }

        total_deduction = 0.0

        # Analyze against skill template if available
        if skill != 'general' and skill in self.skill_templates:
            template = self.skill_templates[skill]
            results['skill_name'] = template['name']

            for angle_name, requirements in template['key_angles'].items():
                # Map template angle names to measured angles
                measured_angle = self._map_template_to_measured(angle_name, angles)

                if measured_angle is not None:
                    ideal = requirements['ideal']
                    tolerance = requirements['tolerance']
                    deviation = abs(measured_angle - ideal)

                    # Calculate deduction
                    deduction = self._calculate_deduction(deviation, tolerance)
                    total_deduction += deduction

                    # Generate feedback
                    if deviation > tolerance:
                        error = {
                            'angle': angle_name,
                            'ideal': ideal,
                            'measured': measured_angle,
                            'deviation': deviation,
                            'deduction': deduction,
                            'description': requirements['description'],
                            'severity': self._get_severity(deviation, tolerance)
                        }
                        results['errors'].append(error)
                    elif deviation > tolerance * 0.5:
                        warning = {
                            'angle': angle_name,
                            'ideal': ideal,
                            'measured': measured_angle,
                            'deviation': deviation,
                            'description': requirements['description']
                        }
                        results['warnings'].append(warning)

        # Check general form criteria
        general_deductions = self._check_general_form(angles)
        total_deduction += general_deductions['total']
        results['errors'].extend(general_deductions['errors'])
        results['warnings'].extend(general_deductions['warnings'])

        # Check for injury risks
        injury_risks = self._check_injury_risks(angles)
        results['injury_risks'] = injury_risks

        # Calculate final score (10.0 is perfect)
        final_score = max(0.0, 10.0 - total_deduction)
        results['score'] = round(final_score, 2)
        results['total_deduction'] = round(total_deduction, 2)

        # Overall quality assessment
        if final_score >= 9.5:
            results['overall_quality'] = 'Excellent'
        elif final_score >= 9.0:
            results['overall_quality'] = 'Very Good'
        elif final_score >= 8.5:
            results['overall_quality'] = 'Good'
        elif final_score >= 8.0:
            results['overall_quality'] = 'Fair'
        else:
            results['overall_quality'] = 'Needs Improvement'

        return results

    def _map_template_to_measured(self, template_name: str, angles: Dict[str, float]) -> Optional[float]:
        """
        Map template angle names to measured angle values.

        Args:
            template_name: Name from template
            angles: Measured angles dictionary

        Returns:
            Measured angle value or None
        """
        # Mapping logic
        if template_name == 'body_vertical' or template_name == 'torso_upright':
            return angles.get('torso_vertical')

        elif template_name == 'shoulder_angle':
            left = angles.get('left_shoulder')
            right = angles.get('right_shoulder')
            if left and right:
                return (left + right) / 2
            return left or right

        elif template_name == 'hip_angle' or template_name == 'hip_elevation':
            left = angles.get('left_hip')
            right = angles.get('right_hip')
            if left and right:
                return (left + right) / 2
            return left or right

        elif template_name == 'knee_angle':
            left = angles.get('left_knee')
            right = angles.get('right_knee')
            if left and right:
                return (left + right) / 2
            return left or right

        elif template_name == 'front_knee':
            return angles.get('left_knee') or angles.get('right_knee')

        elif template_name == 'back_knee':
            return angles.get('right_knee') or angles.get('left_knee')

        elif template_name == 'ankle_point':
            left = angles.get('left_ankle')
            right = angles.get('right_ankle')
            if left and right:
                return (left + right) / 2
            return left or right

        elif template_name == 'leg_split_angle':
            # Approximate split angle from hip angles
            left_hip = angles.get('left_hip')
            right_hip = angles.get('right_hip')
            if left_hip and right_hip:
                return abs(left_hip - right_hip) + min(left_hip, right_hip)
            return None

        return None

    def _calculate_deduction(self, deviation: float, tolerance: float) -> float:
        """
        Calculate score deduction based on deviation from ideal.

        Args:
            deviation: Degrees off from ideal
            tolerance: Acceptable tolerance

        Returns:
            Deduction amount
        """
        if deviation <= tolerance:
            return 0.0

        effective_deviation = deviation - tolerance

        # Apply deduction ranges
        if effective_deviation < DEDUCTION_RANGES['minor'][1]:
            return DEDUCTION_VALUES['minor']
        elif effective_deviation < DEDUCTION_RANGES['moderate'][1]:
            return DEDUCTION_VALUES['moderate']
        elif effective_deviation < DEDUCTION_RANGES['major'][1]:
            return DEDUCTION_VALUES['major']
        else:
            return DEDUCTION_VALUES['severe']

    def _get_severity(self, deviation: float, tolerance: float) -> str:
        """Determine severity level of form error."""
        effective_deviation = deviation - tolerance

        if effective_deviation < DEDUCTION_RANGES['minor'][1]:
            return 'minor'
        elif effective_deviation < DEDUCTION_RANGES['moderate'][1]:
            return 'moderate'
        elif effective_deviation < DEDUCTION_RANGES['major'][1]:
            return 'major'
        else:
            return 'severe'

    def _check_general_form(self, angles: Dict[str, float]) -> Dict:
        """Check general form criteria (pointed toes, straight arms, etc.)."""
        errors = []
        warnings = []
        total_deduction = 0.0

        # Check for pointed toes
        left_ankle = angles.get('left_ankle')
        right_ankle = angles.get('right_ankle')

        if left_ankle and left_ankle < GENERAL_FORM['pointed_toes']['threshold']:
            deviation = GENERAL_FORM['pointed_toes']['threshold'] - left_ankle
            deduction = self._calculate_deduction(deviation, 10)
            total_deduction += deduction
            errors.append({
                'angle': 'left_toes',
                'description': 'Left toes not pointed',
                'measured': left_ankle,
                'deduction': deduction,
                'severity': 'minor'
            })

        if right_ankle and right_ankle < GENERAL_FORM['pointed_toes']['threshold']:
            deviation = GENERAL_FORM['pointed_toes']['threshold'] - right_ankle
            deduction = self._calculate_deduction(deviation, 10)
            total_deduction += deduction
            errors.append({
                'angle': 'right_toes',
                'description': 'Right toes not pointed',
                'measured': right_ankle,
                'deduction': deduction,
                'severity': 'minor'
            })

        # Check for straight arms
        left_elbow = angles.get('left_elbow')
        right_elbow = angles.get('right_elbow')

        if left_elbow and left_elbow < GENERAL_FORM['straight_arms']['threshold']:
            warnings.append({
                'angle': 'left_elbow',
                'description': 'Left arm slightly bent',
                'measured': left_elbow
            })

        if right_elbow and right_elbow < GENERAL_FORM['straight_arms']['threshold']:
            warnings.append({
                'angle': 'right_elbow',
                'description': 'Right arm slightly bent',
                'measured': right_elbow
            })

        return {
            'errors': errors,
            'warnings': warnings,
            'total': total_deduction
        }

    def _check_injury_risks(self, angles: Dict[str, float]) -> List[Dict]:
        """Detect potential injury risks based on form."""
        risks = []

        # Knee hyperextension
        left_knee = angles.get('left_knee')
        right_knee = angles.get('right_knee')

        if left_knee and left_knee > INJURY_RISK_THRESHOLDS['knee_hyperextension']:
            risks.append({
                'type': 'knee_hyperextension',
                'location': 'left_knee',
                'severity': 'high',
                'description': 'Left knee hyperextension detected - risk of ligament injury',
                'recommendation': 'Engage quadriceps, avoid locking knee'
            })

        if right_knee and right_knee > INJURY_RISK_THRESHOLDS['knee_hyperextension']:
            risks.append({
                'type': 'knee_hyperextension',
                'location': 'right_knee',
                'severity': 'high',
                'description': 'Right knee hyperextension detected - risk of ligament injury',
                'recommendation': 'Engage quadriceps, avoid locking knee'
            })

        # Elbow hyperextension
        left_elbow = angles.get('left_elbow')
        right_elbow = angles.get('right_elbow')

        if left_elbow and left_elbow > INJURY_RISK_THRESHOLDS['elbow_hyperextension']:
            risks.append({
                'type': 'elbow_hyperextension',
                'location': 'left_elbow',
                'severity': 'medium',
                'description': 'Left elbow hyperextension detected',
                'recommendation': 'Maintain slight bend in elbow, engage triceps'
            })

        if right_elbow and right_elbow > INJURY_RISK_THRESHOLDS['elbow_hyperextension']:
            risks.append({
                'type': 'elbow_hyperextension',
                'location': 'right_elbow',
                'severity': 'medium',
                'description': 'Right elbow hyperextension detected',
                'recommendation': 'Maintain slight bend in elbow, engage triceps'
            })

        return risks
