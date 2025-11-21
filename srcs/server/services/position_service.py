
from typing import List
from models.position import Position

class PositionService :
    def get_positions(self, department: str = None, min_experience: int = None) -> List[Position]:
        """
        Get a list of positions with optional filtering by department and experience.
        """
        # query = db.session.query(Position)

        if department:
            query = query.filter(Position.department == department)
        if min_experience:
            query = query.filter(Position.experience >= min_experience)

        return query.all()