"""
Employee Service
Business logic for employee management
"""

from typing import List, Dict, Any, Optional
from models.employee import Employee

class EmployeeService:
    """
    Service class handling all employee-related business logic
    Separated from API routes for better maintainability
    """
    
    def __init__(self):
        """Initialize the service with sample data"""
        self.employees: List[Employee] = []
        self.next_id = 1
    
    def create_employee_from_object(self, employee: Employee) -> Dict[str, Any]:
        """Create employee from Employee object"""
        employee.employee_id = self.next_id
        self.next_id += 1
        self.employees.append(employee)
        return employee.to_dict()
    
    def create_employee(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new employee from dictionary data
        
        Args:
            data: Dictionary containing employee information
            
        Returns:
            Dictionary representation of created employee
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Create employee object
        employee = Employee(
            name=data['name'],
            position=data['position'],
            skills=data['skills'],
            experience_years=data.get('experience_years', 0),
            department=data.get('department', 'Unknown')
        )
        
        return self.create_employee_from_object(employee)
    
    def get_employees(self, department: Optional[str] = None, 
                     position: Optional[str] = None,
                     min_experience: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get employees with optional filtering
        
        Args:
            department: Filter by department
            position: Filter by position (partial match)
            min_experience: Minimum years of experience
            
        Returns:
            List of employee dictionaries
        """
        filtered_employees = self.employees.copy()
        
        # Apply filters
        if department:
            filtered_employees = [
                emp for emp in filtered_employees 
                if emp.department.lower() == department.lower()
            ]
        
        if position:
            filtered_employees = [
                emp for emp in filtered_employees
                if position.lower() in emp.position.lower()
            ]
        
        if min_experience is not None:
            filtered_employees = [
                emp for emp in filtered_employees
                if emp.experience_years >= min_experience
            ]
        
        return [emp.to_dict() for emp in filtered_employees]
    
    def get_employee_by_id(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """Get employee by ID"""
        employee = self._find_employee_by_id(employee_id)
        return employee.to_dict() if employee else None
    
    def _find_employee_by_id(self, employee_id: str) -> Optional[Employee]:
        """Find employee object by ID (internal use)"""
        
        for employee in self.employees:
            if employee.employee_id == employee_id:
                return employee
        return None
    
    def update_employee(self, employee_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update employee information
        
        Args:
            employee_id: ID of employee to update
            data: Dictionary with updated fields
            
        Returns:
            Updated employee dictionary or None if not found
        """
        employee = self._find_employee_by_id(employee_id)
        if not employee:
            return None
        
        # Update fields if provided
        if 'name' in data:
            employee.name = data['name']
        if 'position' in data:
            employee.position = data['position']
        if 'department' in data:
            employee.department = data['department']
        if 'experience_years' in data:
            employee.experience_years = data['experience_years']
        if 'skills' in data:
            employee.skills = [skill.lower().strip() for skill in data['skills']]
        
        return employee.to_dict()
    
    def delete_employee(self, employee_id: int) -> bool:
        """
        Delete an employee
        
        Args:
            employee_id: ID of employee to delete
            
        Returns:
            True if deleted, False if not found
        """
        employee = self._find_employee_by_id(employee_id)
        if employee:
            self.employees.remove(employee)
            return True
        return False
    
    def add_skills(self, employee_id: int, skills: List[str]) -> Optional[Dict[str, Any]]:
        """
        Add skills to an employee
        
        Args:
            employee_id: ID of employee
            skills: List of skills to add
            
        Returns:
            Updated employee dictionary or None if not found
        """
        employee = self._find_employee_by_id(employee_id)
        if not employee:
            return None
        
        for skill in skills:
            employee.add_skill(skill)
        
        return employee.to_dict()
    
    def remove_skill(self, employee_id: int, skill: str) -> Optional[Dict[str, Any]]:
        """
        Remove a skill from an employee
        
        Args:
            employee_id: ID of employee
            skill: Skill to remove
            
        Returns:
            Updated employee dictionary or None if not found
        """
        employee = self._find_employee_by_id(employee_id)
        if not employee:
            return None
        
        removed = employee.remove_skill(skill)
        if not removed:
            return None  # Skill not found
        
        return employee.to_dict()
    
    def get_employees_by_department(self, department: str) -> List[Employee]:
        """Get all employees in a specific department (returns objects)"""
        return [
            emp for emp in self.employees
            if emp.department.lower() == department.lower()
        ]
    
    def get_employees_by_skill(self, skill: str) -> List[Employee]:
        """Get all employees who have a specific skill (returns objects)"""
        return [
            emp for emp in self.employees
            if emp.has_skill(skill)
        ]
    
    def get_all_departments(self) -> List[str]:
        """Get list of all unique departments"""
        departments = set(emp.department for emp in self.employees)
        return sorted(list(departments))
    
    def get_all_positions(self) -> List[str]:
        """Get list of all unique positions"""
        positions = set(emp.position for emp in self.employees)
        return sorted(list(positions))
    
    def get_all_skills(self) -> List[str]:
        """Get list of all unique skills"""
        all_skills = set()
        for emp in self.employees:
            all_skills.update(emp.skills)
        return sorted(list(all_skills))
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get basic statistics about employees"""
        if not self.employees:
            return {
                "total_employees": 0,
                "departments": [],
                "positions": [],
                "skills": []
            }
        
        total_experience = sum(emp.experience_years for emp in self.employees)
        avg_experience = total_experience / len(self.employees) if self.employees else 0
        
        return {
            "total_employees": len(self.employees),
            "average_experience": round(avg_experience, 1),
            "departments": self.get_all_departments(),
            "positions": self.get_all_positions(),
            "total_unique_skills": len(self.get_all_skills()),
            "department_counts": self._get_department_counts(),
            "experience_distribution": self._get_experience_distribution()
        }
    
    def _get_department_counts(self) -> Dict[str, int]:
        """Get count of employees per department"""
        dept_counts = {}
        for emp in self.employees:
            dept_counts[emp.department] = dept_counts.get(emp.department, 0) + 1
        return dept_counts
    
    def _get_experience_distribution(self) -> Dict[str, int]:
        """Get distribution of employees by experience level"""
        distribution = {"junior": 0, "mid": 0, "senior": 0, "expert": 0}
        
        for emp in self.employees:
            years = emp.experience_years
            if years < 2:
                distribution["junior"] += 1
            elif years < 5:
                distribution["mid"] += 1
            elif years < 10:
                distribution["senior"] += 1
            else:
                distribution["expert"] += 1
        
        return distribution
