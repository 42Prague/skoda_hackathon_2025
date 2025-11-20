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
        """Retrieve employee data by ID"""
        employee_qualifications = g_data_accesser.get_employee_qualifications(employee.personal_number)
        all_action_types = g_data_accesser.get_action_types()
        if not employee_qualifications or not all_action_types:
            return 0.0
        return len(employee_qualifications) / max(len(all_action_types), 1) * 100.0

    def get_skill_depth(self, employee: Employee) -> float:
        """Mock Skill Depth using formula variant C: 0.5 * count(contents) + 0.5 * total_learning_minutes.
        For MVP: assume each qualification adds 3 content items, each action type record adds 45 minutes.
        """
        quals = g_data_accesser.get_employee_qualifications(employee.personal_number) or []
        contents_count = len(quals) * 3  # mock: 3 pieces per qualification
        # mock minutes from action types (if available)
        action_types = g_data_accesser.get_action_types() or []
        minutes_total = len(quals) * 30 + len(action_types) * 15  # synthetic weighting
        depth = 0.5 * contents_count + 0.5 * minutes_total
        return round(depth, 2)

    def get_learning_intensity(self, employee: Employee) -> float:
        """Mock Learning Intensity for last 12 months.
        Assume subset of qualifications are 'recent': pick last N based on ID hash.
        """
        quals = g_data_accesser.get_employee_qualifications(employee.personal_number) or []
        if not quals:
            return 0.0
        # pseudo selection of recent items
        recent_factor = (hash(employee.personal_number) % 5) + 1
        recent_items = min(len(quals), recent_factor)
        # variant A (count) and B (minutes); choose A for return
        return float(recent_items)

    def get_qualification_strength(self, employee: Employee) -> float:
        """Mock Qualification Strength = count(valid qualifications) with simple weighting.
        Weight rule: if qualification_id numeric and > 1000 add 1.5 else 1.
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
        return round(strength, 2)

    def get_job_requirement_coverage(self, employee: Employee) -> float:
        """Mock Coverage Rate.
        Assume required qualifications set size = 10; coverage = employee quals intersect pseudo required.
        Use hash to create deterministic pseudo required set.
        """
        required_size = 10
        quals = g_data_accesser.get_employee_qualifications(employee.personal_number) or []
        if required_size == 0:
            return 0.0
        # pseudo intersection size based on employee hash
        pseudo_overlap = min(len(quals), (hash(employee.personal_number) % (required_size + 1)))
        coverage = pseudo_overlap / required_size
        return round(coverage, 3)

    def get_skill_gap_index(self, employee: Employee) -> float:
        """Skill gap = 1 - coverage; ensure bounds [0,1]."""
        coverage = self.get_job_requirement_coverage(employee)
        gap = 1.0 - coverage
        return round(max(0.0, min(1.0, gap)), 3)

    def get_recent_learning_index(self, employee: Employee) -> float:
        """Mock Recent Learning Index using exponential decay.
        Assume 5 synthetic learning events with (minutes, months_ago) derived from hash.
        Recent_Learning = Σ (minutes * e^(-α * months_since)), α=0.2.
        """
        import math
        alpha = 0.2
        base = abs(hash(employee.personal_number))
        events = []
        # generate 5 events
        for i in range(5):
            minutes = 30 + (base % 50)  # 30-79
            months_ago = (base // (i + 3)) % 12  # 0-11
            events.append((minutes, months_ago))
        score = sum(m * math.exp(-alpha * months) for m, months in events)
        return round(score, 2)
