"""
Synthetic automotive workforce dataset generator for demos.
"""

from __future__ import annotations

import random
from typing import List

import pandas as pd


DEPARTMENTS = [
    "Powertrain Engineering",
    "Autonomous Systems",
    "Manufacturing",
    "Supply Chain",
    "Connected Services",
    "Design Studio",
    "Quality Assurance",
    "Customer Experience",
]

SKILLS = [
    "Battery Systems",
    "Chassis Design",
    "Embedded C",
    "Autonomous Perception",
    "Vehicle Networking",
    "Predictive Maintenance",
    "Robot Programming",
    "Digital Twins",
    "Supply Planning",
    "Supplier Quality",
    "UX Research",
    "HMI Design",
    "Data Engineering",
    "Cloud Fleet Management",
    "Cybersecurity",
]

ROLES = [
    "Senior Systems Engineer",
    "Autonomous Software Lead",
    "Manufacturing Supervisor",
    "Supply Strategist",
    "Connected Vehicle PM",
    "Design Technologist",
    "Quality Lead",
    "Customer Programs Manager",
]

LOCATIONS = ["Mladá Boleslav", "Prague", "Bratislava", "Pune", "Barcelona", "Shanghai"]


def _random_skills() -> List[str]:
    return random.sample(SKILLS, k=random.randint(4, 7))


def generate_demo_dataset(employee_count: int = 60) -> pd.DataFrame:
    """Generate a deterministic-looking automotive workforce dataset."""
    random.seed(employee_count)
    rows = []
    for idx in range(1, employee_count + 1):
        department = random.choice(DEPARTMENTS)
        rows.append(
            {
                "employee_id": f"EMP{idx:04d}",
                "name": f"Demo Employee {idx}",
                "department": department,
                "skills": ", ".join(_random_skills()),
                "role": random.choice(ROLES),
                "seniority": random.choice(["Junior", "Mid", "Senior", "Lead"]),
                "location": random.choice(LOCATIONS),
            }
        )
    return pd.DataFrame(rows)

