"""
Skill Analyzer
This class handles all the logic for analyzing employee skills and making suggestions.
"""

from typing import List, Dict, Any, Optional
from models.employee import Employee
import json
from collections import Counter
from data.data_accesser import g_data_accesser

class SkillAnalyzer:
    """
    Main class for analyzing employee skills and providing suggestions
    """
    
    def __init__(self):
        """Initialize the analyzer with sample data"""
        self.employees: List[Employee] = []
        self.next_id = 1
    
    def get_breadth(self, employee: Employee) -> float:
        """Breadth scaled 1..10 using sqrt expansion.
        0 if no data; else min score 1 and max 10.
        """
        employee_qualifications = g_data_accesser.get_employee_qualifications(employee.personal_number)
        all_action_types = g_data_accesser.get_action_types()
        if not employee_qualifications or not all_action_types:
            return 0.0  # no data at all
        raw_ratio = len(employee_qualifications) / max(len(all_action_types), 1)  # 0..1
        if raw_ratio <= 0:
            return 0.0
        # Non-linear stretch: sqrt gives higher weight to early progress.
        score = 1 + 9 * (raw_ratio ** 0.5)  # raw_ratio=1 => 10, tiny ratio => ~1
        if score > 10:
            score = 10.0
        return round(score, 2)

    def get_skill_depth(self, employee: Employee) -> float:
        """Return 0-10 scaled skill depth.
        Assume theoretical max depth ~ 1000 for mock scaling.
        """
        quals = g_data_accesser.get_employee_qualifications(employee.personal_number) or []
        action_types = g_data_accesser.get_action_types() or []
        contents_count = len(quals) * 3
        minutes_total = len(quals) * 30 + len(action_types) * 15
        raw_depth = 0.5 * contents_count + 0.5 * minutes_total
        max_depth = 1000.0
        return round(min(raw_depth / max_depth * 10.0, 10.0), 2)

    def get_learning_intensity(self, employee: Employee) -> float:
        """Return 0-10 scaled learning intensity.
        Assume max recent items of interest = 12 in period.
        """
        quals = g_data_accesser.get_employee_qualifications(employee.personal_number) or []
        if not quals:
            return 0.0
        recent_factor = (hash(employee.personal_number) % 5) + 1
        recent_items = min(len(quals), recent_factor)
        max_items = 12.0
        return round(recent_items / max_items * 10.0, 2)

    def get_qualification_strength(self, employee: Employee) -> float:
        """Return 0-10 scaled qualification strength.
        Assume max effective strength cap = 30.
        """
        quals = g_data_accesser.get_employee_qualifications(employee.personal_number) or []
        strength = 0.0
        for q in quals:
            qid = getattr(q, 'qualification_id', None)
            try:
                val = int(qid) if qid is not None else 0
            except ValueError:
                val = 0
            strength += 1.5 if val > 1000 else 1.0
        max_strength = 30.0
        return round(min(strength / max_strength * 10.0, 10.0), 2)

    def get_job_requirement_coverage(self, employee: Employee) -> float:
        required_size = 10
        quals = g_data_accesser.get_employee_qualifications(employee.personal_number) or []
        if required_size == 0:
            return 0.0
        pseudo_overlap = min(len(quals), (hash(employee.personal_number) % (required_size + 1)))
        coverage = pseudo_overlap / required_size  # 0..1
        return round(coverage * 10.0, 2)

    def get_skill_gap_index(self, employee: Employee) -> float:
        coverage_0_10 = self.get_job_requirement_coverage(employee)
        # coverage_0_10 is already scaled; convert back to fraction then gap then rescale
        coverage_fraction = coverage_0_10 / 10.0
        gap_fraction = 1.0 - coverage_fraction
        return round(gap_fraction * 10.0, 2)

    def get_recent_learning_index(self, employee: Employee) -> float:
        import math
        alpha = 0.2
        base = abs(hash(employee.personal_number))
        events = []
        for i in range(5):
            minutes = 30 + (base % 50)
            months_ago = (base // (i + 3)) % 12
            events.append((minutes, months_ago))
        score = sum(m * math.exp(-alpha * months) for m, months in events)
        # Assume max recent learning score ~ 300 for scaling
        max_score = 300.0
        return round(min(score / max_score * 10.0, 10.0), 2)
