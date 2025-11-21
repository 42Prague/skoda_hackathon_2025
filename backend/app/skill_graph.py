import logging
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import pandas as pd
import networkx as nx
from config import settings

logger = logging.getLogger(__name__)


class SkillGraph:
    def __init__(self):
        """Initialize an empty directed graph."""
        self.graph = nx.DiGraph()
        logger.info("Initialized empty skill graph")

    def add_employees(self, employees_df: pd.DataFrame):
        if employees_df is None or employees_df.empty:
            logger.warning("No employee data to add")
            return

        for _, row in employees_df.iterrows():
            personal_number = row.get('personal_number')
            if pd.isna(personal_number):
                continue

            self.graph.add_node(
                f"emp:{personal_number}",
                node_type='employee',
                personal_number=str(personal_number),
                profession=row.get('profession'),
                planned_position=row.get('planned_position'),
                org_unit=row.get('org_unit')
            )

            # Add edge to org unit if present
            org_unit = row.get('org_unit')
            if not pd.isna(org_unit):
                self.graph.add_node(f"org:{org_unit}", node_type='org_unit', objid=str(org_unit))
                self.graph.add_edge(f"emp:{personal_number}", f"org:{org_unit}", edge_type='WORKS_IN')

            # Add edge to planned position if present
            planned_pos = row.get('planned_position')
            if not pd.isna(planned_pos):
                self.graph.add_node(f"pos:{planned_pos}", node_type='position', position_id=str(planned_pos))
                self.graph.add_edge(f"emp:{personal_number}", f"pos:{planned_pos}", edge_type='PLANNED_FOR')

        logger.info(f"Added {len(employees_df)} employee nodes")

    def add_skills(self, skills_df: pd.DataFrame):
        if skills_df is None or skills_df.empty:
            logger.warning("No skill data to add")
            return

        for _, row in skills_df.iterrows():
            skill_id = row.get('skillid')
            if pd.isna(skill_id):
                continue

            self.graph.add_node(
                f"skill:{skill_id}",
                node_type='skill',
                skill_id=str(skill_id),
                name=row.get('name'),
                description=row.get('description')
            )

        logger.info(f"Added {len(skills_df)} skill nodes")

    def add_qualifications(self, qualifications_df: pd.DataFrame):
        if qualifications_df is None or qualifications_df.empty:
            logger.warning("No qualification data to add")
            return

        edge_count = 0
        for _, row in qualifications_df.iterrows():
            personal_number = row.get('personal_number')
            id_q = row.get('id_q')

            if pd.isna(personal_number) or pd.isna(id_q):
                continue

            # Add qualification node if not exists
            qual_node = f"qual:{id_q}"
            if qual_node not in self.graph:
                self.graph.add_node(
                    qual_node,
                    node_type='qualification',
                    qualification_id=str(id_q),
                    name=row.get('name_q')
                )

            # Add edge from employee to qualification
            emp_node = f"emp:{personal_number}"
            # Create employee node if it doesn't exist
            if emp_node not in self.graph:
                self.graph.add_node(
                    emp_node,
                    node_type='employee',
                    personal_number=str(personal_number)
                )
            
            self.graph.add_edge(
                emp_node,
                qual_node,
                edge_type='HAS_QUALIFICATION',
                start_date=row.get('start_date'),
                end_date=row.get('end_date'),
                is_indefinite=row.get('is_indefinite', False)
            )
            edge_count += 1

        logger.info(f"Added {edge_count} qualification edges")

    def add_course_participation(self, course_participation_df: pd.DataFrame):
        if course_participation_df is None or course_participation_df.empty:
            logger.warning("No course participation data to add")
            return

        edge_count = 0
        for _, row in course_participation_df.iterrows():
            personal_number = row.get('personal_number')
            course_id = row.get('idobj')

            if pd.isna(personal_number) or pd.isna(course_id):
                continue

            # Add course node if not exists
            course_node = f"course:{course_id}"
            if course_node not in self.graph:
                self.graph.add_node(
                    course_node,
                    node_type='course',
                    course_id=str(course_id),
                    name=row.get('oznaceni_typu_akce')
                )

            # Add edge from employee to course
            emp_node = f"emp:{personal_number}"
            # Create employee node if it doesn't exist
            if emp_node not in self.graph:
                self.graph.add_node(
                    emp_node,
                    node_type='employee',
                    personal_number=str(personal_number)
                )
            
            self.graph.add_edge(
                emp_node,
                course_node,
                edge_type='COMPLETED_COURSE',
                start_date=row.get('datum_zahajeni'),
                end_date=row.get('datum_ukonceni')
            )
            edge_count += 1

        logger.info(f"Added {edge_count} course completion edges")

    def add_skill_mappings(self, skill_mapping_df: pd.DataFrame):
        if skill_mapping_df is None or skill_mapping_df.empty:
            logger.warning("No skill mapping data to add")
            return

        edge_count = 0
        for _, row in skill_mapping_df.iterrows():
            course_id = row.get('course_id')
            skill_id = row.get('skill_id')

            if pd.isna(course_id) or pd.isna(skill_id):
                continue

            course_node = f"course:{course_id}"
            skill_node = f"skill:{skill_id}"

            # Ensure both nodes exist
            if course_node not in self.graph:
                self.graph.add_node(course_node, node_type='course', course_id=str(course_id))

            if skill_node not in self.graph:
                self.graph.add_node(
                    skill_node,
                    node_type='skill',
                    skill_id=str(skill_id),
                    name=row.get('skill_name')
                )

            # Add edge
            self.graph.add_edge(course_node, skill_node, edge_type='DEVELOPS_SKILL')
            edge_count += 1

        logger.info(f"Added {edge_count} course->skill mapping edges")

    def add_role_requirements(self, role_qualifications_df: pd.DataFrame):
        if role_qualifications_df is None or role_qualifications_df.empty:
            logger.warning("No role qualification requirements to add")
            return

        edge_count = 0
        for _, row in role_qualifications_df.iterrows():
            position_id = row.get('planned_position_id')
            qual_id = row.get('id_kvalifikace')

            if pd.isna(position_id) or pd.isna(qual_id):
                continue

            pos_node = f"pos:{position_id}"
            qual_node = f"qual:{qual_id}"

            # Ensure nodes exist
            if pos_node not in self.graph:
                self.graph.add_node(pos_node, node_type='position', position_id=str(position_id))

            if qual_node not in self.graph:
                self.graph.add_node(
                    qual_node,
                    node_type='qualification',
                    qualification_id=str(qual_id),
                    name=row.get('kvalifikace')
                )

            # Add edge
            self.graph.add_edge(pos_node, qual_node, edge_type='REQUIRES_QUALIFICATION')
            edge_count += 1

        logger.info(f"Added {edge_count} position->qualification requirement edges")

    def add_org_hierarchy(self, org_structure_df: pd.DataFrame):
        if org_structure_df is None or org_structure_df.empty:
            logger.warning("No org structure data to add")
            return

        edge_count = 0
        for _, row in org_structure_df.iterrows():
            objid = row.get('objid')
            parent = row.get('paren')

            if pd.isna(objid):
                continue

            # Add/update org unit node
            org_node = f"org:{objid}"
            self.graph.add_node(
                org_node,
                node_type='org_unit',
                objid=str(objid),
                short=row.get('short'),
                name_en=row.get('stxte')
            )

            # Add parent relationship
            if not pd.isna(parent):
                parent_node = f"org:{parent}"
                if parent_node not in self.graph:
                    self.graph.add_node(parent_node, node_type='org_unit', objid=str(parent))

                self.graph.add_edge(parent_node, org_node, edge_type='PARENT_OF')
                edge_count += 1

        logger.info(f"Added {edge_count} org hierarchy edges")

    def get_employee_skills(self, personal_number: str) -> List[Dict]:
        emp_node = f"emp:{personal_number}"
        if emp_node not in self.graph:
            logger.warning(f"Employee {personal_number} not found in graph")
            return []

        skills = []

        # Traverse: employee -> course -> skill
        for course_node in self.graph.successors(emp_node):
            if self.graph.nodes[course_node].get('node_type') == 'course':
                for skill_node in self.graph.successors(course_node):
                    if self.graph.nodes[skill_node].get('node_type') == 'skill':
                        skill_data = self.graph.nodes[skill_node]
                        skills.append({
                            'skill_id': skill_data.get('skill_id'),
                            'name': skill_data.get('name'),
                            'acquired_via_course': self.graph.nodes[course_node].get('course_id')
                        })

        return skills

    def get_employee_qualifications(self, personal_number: str) -> List[Dict]:
        emp_node = f"emp:{personal_number}"
        if emp_node not in self.graph:
            return []

        qualifications = []
        for qual_node in self.graph.successors(emp_node):
            if self.graph.nodes[qual_node].get('node_type') == 'qualification':
                qual_data = self.graph.nodes[qual_node]
                edge_data = self.graph.edges[emp_node, qual_node]
                qualifications.append({
                    'qualification_id': qual_data.get('qualification_id'),
                    'name': qual_data.get('name'),
                    'start_date': edge_data.get('start_date'),
                    'end_date': edge_data.get('end_date'),
                    'is_indefinite': edge_data.get('is_indefinite')
                })

        return qualifications

    def get_missing_qualifications(self, personal_number: str) -> List[Dict]:
        """
        Get qualifications required for employee's planned position that they don't have.
        """
        emp_node = f"emp:{personal_number}"
        if emp_node not in self.graph:
            return []

        # Find planned position
        planned_position = None
        for pos_node in self.graph.successors(emp_node):
            if self.graph.nodes[pos_node].get('node_type') == 'position':
                planned_position = pos_node
                break

        if not planned_position:
            logger.info(f"No planned position for employee {personal_number}")
            return []

        # Get required qualifications for position
        required_quals = set()
        for qual_node in self.graph.successors(planned_position):
            if self.graph.nodes[qual_node].get('node_type') == 'qualification':
                required_quals.add(qual_node)

        # Get employee's current qualifications
        current_quals = set()
        for qual_node in self.graph.successors(emp_node):
            if self.graph.nodes[qual_node].get('node_type') == 'qualification':
                current_quals.add(qual_node)

        # Find missing
        missing = required_quals - current_quals

        missing_list = []
        for qual_node in missing:
            qual_data = self.graph.nodes[qual_node]
            missing_list.append({
                'qualification_id': qual_data.get('qualification_id'),
                'name': qual_data.get('name')
            })

        return missing_list

    def get_courses_for_skill(self, skill_id: str) -> List[Dict]:
        skill_node = f"skill:{skill_id}"
        if skill_node not in self.graph:
            return []

        courses = []
        # Find predecessors (courses that point to this skill)
        for course_node in self.graph.predecessors(skill_node):
            if self.graph.nodes[course_node].get('node_type') == 'course':
                course_data = self.graph.nodes[course_node]
                courses.append({
                    'course_id': course_data.get('course_id'),
                    'name': course_data.get('name')
                })

        return courses

    def get_stats(self) -> Dict:
        node_types = {}
        for node, data in self.graph.nodes(data=True):
            node_type = data.get('node_type', 'unknown')
            node_types[node_type] = node_types.get(node_type, 0) + 1

        edge_types = {}
        for u, v, data in self.graph.edges(data=True):
            edge_type = data.get('edge_type', 'unknown')
            edge_types[edge_type] = edge_types.get(edge_type, 0) + 1

        return {
            'total_nodes': self.graph.number_of_nodes(),
            'total_edges': self.graph.number_of_edges(),
            'node_types': node_types,
            'edge_types': edge_types
        }

    def save(self, path: Optional[Path] = None):
        if path is None:
            path = settings.graph_state_path

        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'wb') as f:
            pickle.dump(self.graph, f)

        logger.info(f"Saved skill graph to {path}")

    @classmethod
    def load(cls, path: Optional[Path] = None) -> 'SkillGraph':
        """Load graph from disk."""
        if path is None:
            path = settings.graph_state_path

        if not path.exists():
            logger.warning(f"Graph file not found at {path}, returning empty graph")
            return cls()

        instance = cls()
        with open(path, 'rb') as f:
            instance.graph = pickle.load(f)

        logger.info(f"Loaded skill graph from {path}")
        return instance


def build_graph_from_parquet() -> SkillGraph:
    logger.info("Building skill graph from Parquet files...")

    parquet_dir = settings.clean_parquet_dir

    graph = SkillGraph()

    # Load datasets
    datasets = {}
    for parquet_file in parquet_dir.glob("*.parquet"):
        dataset_name = parquet_file.stem
        try:
            datasets[dataset_name] = pd.read_parquet(parquet_file)
            logger.info(f"Loaded {dataset_name}: {len(datasets[dataset_name])} rows")
        except Exception as e:
            logger.error(f"Failed to load {parquet_file}: {e}")

    # Build graph in order
    if 'employees' in datasets:
        graph.add_employees(datasets['employees'])

    if 'skill_dictionary' in datasets:
        graph.add_skills(datasets['skill_dictionary'])

    if 'qualifications' in datasets:
        graph.add_qualifications(datasets['qualifications'])

    if 'course_participation' in datasets:
        graph.add_course_participation(datasets['course_participation'])

    if 'skill_mapping' in datasets:
        graph.add_skill_mappings(datasets['skill_mapping'])

    if 'role_qualifications' in datasets:
        graph.add_role_requirements(datasets['role_qualifications'])

    if 'org_structure' in datasets:
        graph.add_org_hierarchy(datasets['org_structure'])

    # Log stats
    stats = graph.get_stats()
    logger.info(f"Graph statistics: {stats}")

    # Save graph
    graph.save()

    return graph


if __name__ == "__main__":
    # Build and save graph
    graph = build_graph_from_parquet()
    print("Graph built successfully!")
    print(f"Stats: {graph.get_stats()}")
