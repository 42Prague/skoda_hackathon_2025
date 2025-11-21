"""Skill hierarchy inference for parent-child relationships."""

import logging
from typing import List, Dict, Set, Tuple
import re
import json

from rich.console import Console

from src.models import NormalizedSkill
from src.extraction.llm_client import llm_client

logger = logging.getLogger(__name__)
console = Console()


class SkillHierarchyBuilder:
    """Builds hierarchical relationships between skills."""

    def __init__(self):
        """Initialize the hierarchy builder."""
        from pathlib import Path
        from config.settings import settings

        # Cache file for LLM-inferred hierarchies
        self.cache_file = settings.data_dir / "llm_hierarchy_cache.json"
        self.hierarchy_cache: Dict[str, List[Tuple[str, str]]] = {}
        self._load_cache()

        # Define common parent-child relationships
        self.known_hierarchies = {
            # Programming Languages
            "Python": [
                "Django", "Flask", "FastAPI", "Pandas", "NumPy", "PyTorch",
                "TensorFlow", "Scikit-learn", "Scrapy", "Celery"
            ],
            "JavaScript": [
                "React", "Vue.js", "Angular", "Node.js", "Express.js",
                "Next.js", "TypeScript", "jQuery", "Webpack", "Babel"
            ],
            "Java": [
                "Spring", "Spring Boot", "Hibernate", "Maven", "Gradle",
                "JUnit", "JSP", "Servlets"
            ],
            "Ruby": ["Rails", "Ruby on Rails", "Sinatra", "RSpec"],
            "PHP": ["Laravel", "Symfony", "WordPress", "Drupal", "CodeIgniter"],
            "C#": ["ASP.NET", ".NET", "Entity Framework", "Unity", "Xamarin"],
            "Go": ["Gin", "Echo", "Beego"],
            "Rust": ["Actix", "Rocket", "Tokio"],

            # Cloud Platforms
            "AWS": [
                "EC2", "S3", "Lambda", "RDS", "DynamoDB", "CloudFormation",
                "ECS", "EKS", "CloudWatch"
            ],
            "Azure": [
                "Azure Functions", "Azure SQL", "Azure DevOps", "Azure AD",
                "Azure Kubernetes Service"
            ],
            "GCP": [
                "Google Cloud Platform", "BigQuery", "Cloud Functions",
                "Google Kubernetes Engine", "Cloud Storage"
            ],

            # Containers & Orchestration
            "Docker": ["Docker Compose", "Docker Swarm"],
            "Kubernetes": ["Helm", "Kubectl", "K8s"],

            # Databases
            "SQL": [
                "MySQL", "PostgreSQL", "SQL Server", "Oracle", "MariaDB"
            ],
            "NoSQL": [
                "MongoDB", "Cassandra", "Redis", "Elasticsearch",
                "DynamoDB", "Couchbase"
            ],

            # Data & ML
            "Machine Learning": [
                "Deep Learning", "Neural Networks", "NLP", "Computer Vision",
                "TensorFlow", "PyTorch", "Scikit-learn"
            ],
            "Data Science": [
                "Machine Learning", "Statistics", "Data Analysis",
                "Data Visualization", "Pandas", "NumPy"
            ],

            # DevOps & Tools
            "CI/CD": [
                "Jenkins", "GitLab CI", "GitHub Actions", "CircleCI",
                "Travis CI", "Azure DevOps"
            ],
            "Version Control": ["Git", "GitHub", "GitLab", "Bitbucket"],

            # Testing
            "Testing": [
                "Unit Testing", "Integration Testing", "E2E Testing",
                "JUnit", "pytest", "Jest", "Mocha", "Selenium"
            ],

            # Methodologies
            "Agile": ["Scrum", "Kanban", "Sprint Planning", "Stand-ups"],
        }

    def _load_cache(self) -> None:
        """Load cached LLM-inferred hierarchies from disk."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r") as f:
                    data = json.load(f)
                    # Convert list format to dict format
                    # Cache format: {"skill_set_hash": [["parent", "child"], ...]}
                    self.hierarchy_cache = {
                        k: [tuple(v) for v in vals] for k, vals in data.items()
                    }
                logger.info(f"Loaded {len(self.hierarchy_cache)} cached hierarchy sets")
            except Exception as e:
                logger.warning(f"Failed to load hierarchy cache: {e}")

    def _save_cache(self) -> None:
        """Save LLM-inferred hierarchies cache to disk."""
        try:
            # Convert tuples to lists for JSON serialization
            cache_data = {
                k: [list(v) for v in vals] for k, vals in self.hierarchy_cache.items()
            }
            with open(self.cache_file, "w") as f:
                json.dump(cache_data, f, indent=2)
            logger.info(f"Saved hierarchy cache with {len(self.hierarchy_cache)} sets")
        except Exception as e:
            logger.warning(f"Failed to save hierarchy cache: {e}")

    def _get_skill_set_hash(self, skill_names: List[str]) -> str:
        """Generate a hash for a set of skill names."""
        import hashlib
        # Sort for consistent hashing
        sorted_skills = sorted(skill_names)
        skills_str = "|".join(sorted_skills)
        return hashlib.md5(skills_str.encode()).hexdigest()

    def _normalize_skill_name(self, name: str) -> str:
        """Normalize skill name for comparison."""
        # Remove special characters, convert to lowercase
        normalized = re.sub(r'[^\w\s]', '', name.lower())
        # Remove common suffixes
        normalized = re.sub(r'\s+(js|lang|language|framework)$', '', normalized)
        return normalized.strip()

    def _infer_with_llm(
        self,
        normalized_skills: List[NormalizedSkill],
        known_hierarchies: List[Tuple[str, str]]
    ) -> Set[Tuple[str, str]]:
        """Use LLM to infer parent-child hierarchies for all skills.

        Args:
            normalized_skills: All normalized skills
            known_hierarchies: Already known hierarchies as reference

        Returns:
            Set of (parent, child) tuples inferred by LLM
        """
        import asyncio

        # Prepare skill names list
        skill_names = [s.canonical_name for s in normalized_skills]

        # Check cache first
        skill_set_hash = self._get_skill_set_hash(skill_names)
        if skill_set_hash in self.hierarchy_cache:
            logger.info("Using cached LLM hierarchy inference")
            console.print("[cyan]  ✓ Using cached LLM hierarchies[/cyan]")
            return set(self.hierarchy_cache[skill_set_hash])

        # Prepare known hierarchies as examples
        known_examples = [f"{parent} -> {child}" for parent, child in known_hierarchies[:20]]

        prompt = f"""You are a technical skill taxonomy expert. Given a list of technical skills, identify parent-child relationships where one skill is a more specific version, framework, or tool of another.

Skills to analyze:
{json.dumps(skill_names, indent=2)}

Known hierarchy examples for reference:
{chr(10).join(known_examples)}

Rules:
1. Only create hierarchies where there's a clear parent-child relationship
2. Parent is the broader/more general skill (e.g., "Python" is parent of "Django")
3. Child is the more specific framework/library/tool (e.g., "Django" is child of "Python")
4. Do NOT create hierarchies for unrelated skills
5. Consider domain knowledge (e.g., "React" is a JavaScript library, "Docker" is a containerization tool)
6. Only return relationships between skills in the provided list

Return ONLY a JSON array of relationships in this exact format:
[
  {{"parent": "Python", "child": "Django"}},
  {{"parent": "AWS", "child": "EC2"}},
  ...
]

Return an empty array [] if no clear hierarchies exist."""

        try:
            # Call LLM
            async def _call():
                response = await llm_client._call_llm(prompt)
                return response

            response = asyncio.run(_call())

            # Parse response
            response_text = response.strip()

            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            hierarchies_data = json.loads(response_text)

            # Convert to set of tuples
            hierarchies = set()
            skill_names_set = set(skill_names)

            for item in hierarchies_data:
                parent = item.get("parent")
                child = item.get("child")

                # Validate both skills exist in our list
                if parent in skill_names_set and child in skill_names_set and parent != child:
                    hierarchies.add((parent, child))

            # Cache the result
            self.hierarchy_cache[skill_set_hash] = list(hierarchies)
            self._save_cache()

            return hierarchies

        except Exception as e:
            logger.error(f"LLM hierarchy inference failed: {e}")
            return set()

    def infer_hierarchies(
        self, normalized_skills: List[NormalizedSkill]
    ) -> List[Tuple[str, str]]:
        """Infer parent-child relationships between skills.

        Args:
            normalized_skills: List of normalized skills

        Returns:
            List of (parent_name, child_name) tuples
        """
        console.print("\n[bold cyan]Inferring Skill Hierarchies[/bold cyan]")

        hierarchies: Set[Tuple[str, str]] = set()
        skill_names = {s.canonical_name for s in normalized_skills}

        # Build name -> skill mapping for quick lookup
        skill_map = {s.canonical_name: s for s in normalized_skills}

        # Also include aliases in the lookup
        alias_to_canonical: Dict[str, str] = {}
        for skill in normalized_skills:
            alias_to_canonical[skill.canonical_name.lower()] = skill.canonical_name
            for alias in skill.aliases:
                alias_to_canonical[alias.lower()] = skill.canonical_name

        def resolve_skill_name(name: str) -> str | None:
            """Resolve skill name to canonical name."""
            # Try exact match
            if name in skill_names:
                return name

            # Try alias match
            canonical = alias_to_canonical.get(name.lower())
            if canonical:
                return canonical

            return None

        # 1. Apply known hierarchies
        for parent_name, children in self.known_hierarchies.items():
            parent_canonical = resolve_skill_name(parent_name)

            if not parent_canonical:
                continue

            for child_name in children:
                child_canonical = resolve_skill_name(child_name)

                if child_canonical and child_canonical != parent_canonical:
                    hierarchies.add((parent_canonical, child_canonical))

        console.print(f"[cyan]  ✓ Applied {len(hierarchies)} known hierarchies[/cyan]")

        # 2. Use LLM to infer hierarchies for ALL skills
        # Send all skills to LLM for comprehensive hierarchy inference
        console.print("[cyan]  Analyzing skill hierarchies with LLM...[/cyan]")
        llm_hierarchies = self._infer_with_llm(normalized_skills, list(hierarchies))

        # Add LLM-inferred hierarchies (LLM might add new ones or skip some from known)
        for parent, child in llm_hierarchies:
            hierarchies.add((parent, child))

        console.print(f"[cyan]  ✓ Inferred {len(llm_hierarchies)} hierarchies using LLM[/cyan]")

        # Convert to list
        hierarchy_list = list(hierarchies)

        console.print(f"[green]✓ Total hierarchies: {len(hierarchy_list)}[/green]")

        return hierarchy_list

    def print_hierarchy_tree(
        self,
        normalized_skills: List[NormalizedSkill],
        hierarchies: List[Tuple[str, str]],
        max_depth: int = 3,
    ) -> None:
        """Print skill hierarchy as a tree structure.

        Args:
            normalized_skills: List of normalized skills
            hierarchies: List of (parent, child) relationships
            max_depth: Maximum depth to display
        """
        # Build parent -> children mapping
        children_map: Dict[str, List[str]] = {}
        parent_map: Dict[str, str] = {}

        for parent, child in hierarchies:
            if parent not in children_map:
                children_map[parent] = []
            children_map[parent].append(child)
            parent_map[child] = parent

        # Find root skills (skills with no parents)
        all_skills = {s.canonical_name for s in normalized_skills}
        root_skills = all_skills - set(parent_map.keys())

        # Only show roots that have children
        root_skills_with_children = [r for r in root_skills if r in children_map]

        if not root_skills_with_children:
            console.print("[yellow]No hierarchical relationships to display[/yellow]")
            return

        console.print("\n[bold cyan]Skill Hierarchy Tree (sample):[/bold cyan]")

        def print_tree(skill: str, depth: int = 0, prefix: str = ""):
            """Recursively print tree structure."""
            if depth > max_depth:
                return

            indent = "  " * depth
            branch = "├── " if depth > 0 else ""

            console.print(f"{indent}{branch}{skill}")

            if skill in children_map:
                for i, child in enumerate(sorted(children_map[skill])):
                    is_last = i == len(children_map[skill]) - 1
                    print_tree(child, depth + 1, prefix + ("    " if is_last else "│   "))

        # Print top 5 root skills with most children
        roots_sorted = sorted(
            root_skills_with_children,
            key=lambda r: len(children_map.get(r, [])),
            reverse=True,
        )

        for root in roots_sorted[:5]:
            print_tree(root)
            console.print()


# Global hierarchy builder instance
hierarchy_builder = SkillHierarchyBuilder()
