"""
Employee Model
Represents an employee record enriched with HR/ERP metadata.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Employee:
    """Rich employee record based on ERP_SK1.Start_month - SE.

    This model is intentionally close to the source system structure
    so it can be populated directly from ERP exports or APIs.
    """

    personal_number: str
    persstat_ob1: Optional[str] = None
    persstat_ob2: Optional[str] = None
    persstat_ob3: Optional[str] = None
    persstat_ob5: Optional[str] = None
    persstat_ob8: Optional[str] = None
    sa_org_hierarchy_objid: Optional[str] = None
    profession_id: Optional[str] = None
    profession: Optional[str] = None
    planned_profession_id: Optional[str] = None
    planned_profession: Optional[str] = None
    planned_position_id: Optional[str] = None
    planned_position: Optional[str] = None
    basic_branch_of_education_group: Optional[str] = None
    basic_branch_of_education_group2: Optional[str] = None
    basic_branch_of_education_id: Optional[str] = None
    basic_branch_of_education_name: Optional[str] = None
    education_category_id: Optional[str] = None
    education_category_name: Optional[str] = None
    field_of_study_id: Optional[str] = None
    field_of_study_name: Optional[str] = None
    field_of_study_code_ispv: Optional[str] = None
    employee_id: Optional[int] = None
