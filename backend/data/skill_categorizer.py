"""
Automatic Skill Categorization System
Assigns skills to categories based on keywords and patterns
"""
from typing import Dict, Optional
import re

class SkillCategorizer:
    """
    Automatically categorizes skills into:
    - legacy_engineering: Traditional engineering (CAD, mechanical, manufacturing)
    - software_cloud: Software development and cloud (Python, React, AWS, Docker)
    - e_mobility: Electric vehicle technology (battery, powertrain, charging)
    - ai_emerging: AI and machine learning (TensorFlow, PyTorch, NLP, computer vision)
    """

    # Category keywords (case-insensitive)
    CATEGORY_KEYWORDS = {
        'legacy_engineering': [
            'cad', 'catia', 'autocad', 'solidworks', 'mechanical', 'cnc',
            'manufacturing', 'quality control', 'machining', 'assembly',
            'welding', 'tooling', 'design engineer', 'production', 'plc',
            'maintenance', 'fabrication', 'testing', 'inspection'
        ],

        'software_cloud': [
            'python', 'javascript', 'java', 'c++', 'c#', 'react', 'angular',
            'vue', 'node', 'express', 'django', 'flask', 'spring',
            'aws', 'azure', 'gcp', 'cloud', 'docker', 'kubernetes',
            'ci/cd', 'jenkins', 'gitlab', 'github', 'devops',
            'microservices', 'api', 'rest', 'graphql', 'sql', 'nosql',
            'mongodb', 'postgresql', 'mysql', 'redis', 'kafka',
            'agile', 'scrum', 'frontend', 'backend', 'fullstack',
            'web development', 'software', 'programming'
        ],

        'e_mobility': [
            'battery', 'electric', 'powertrain', 'charging', 'energy management',
            'thermal management', 'ev', 'hybrid', 'lithium', 'bms',
            'inverter', 'motor control', 'regenerative braking',
            'charging infrastructure', 'fast charging', 'dc charging',
            'electric vehicle', 'electrification', 'power electronics'
        ],

        'ai_emerging': [
            'machine learning', 'deep learning', 'neural network',
            'tensorflow', 'pytorch', 'keras', 'scikit', 'pandas',
            'numpy', 'nlp', 'computer vision', 'llm', 'gpt',
            'transformers', 'reinforcement learning', 'supervised',
            'unsupervised', 'classification', 'regression', 'clustering',
            'ai', 'artificial intelligence', 'data science', 'analytics',
            'opencv', 'yolo', 'bert', 'generative ai'
        ]
    }

    @classmethod
    def categorize(cls, skill_name: str) -> str:
        """
        Automatically categorize a skill based on keywords

        Args:
            skill_name: Skill name (e.g., "Python", "Battery Systems")

        Returns:
            Category: 'legacy_engineering', 'software_cloud', 'e_mobility', 'ai_emerging', or 'General'
        """
        skill_lower = skill_name.lower().strip()

        # Check each category's keywords
        for category, keywords in cls.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in skill_lower:
                    return category

        # Default category if no match
        return 'General'

    @classmethod
    def bulk_categorize(cls, skills: list) -> Dict[str, str]:
        """
        Categorize multiple skills at once

        Args:
            skills: List of skill names

        Returns:
            Dict mapping {skill_name: category}
        """
        return {skill: cls.categorize(skill) for skill in skills}

    @classmethod
    def get_category_stats(cls, skills: list) -> Dict[str, int]:
        """
        Get category distribution statistics

        Args:
            skills: List of skill names

        Returns:
            Dict with counts per category
        """
        categorized = cls.bulk_categorize(skills)
        stats = {}

        for category in categorized.values():
            stats[category] = stats.get(category, 0) + 1

        return stats


# Convenience function for single skill
def categorize_skill(skill_name: str) -> str:
    """Categorize a single skill"""
    return SkillCategorizer.categorize(skill_name)


if __name__ == "__main__":
    # Test categorizer
    test_skills = [
        "Python", "React", "AWS", "Docker",
        "CAD", "Mechanical Design", "CNC Programming",
        "Battery Systems", "Electric Powertrain",
        "Machine Learning", "TensorFlow", "Computer Vision",
        "Random Skill Name"
    ]

    print("🧠 Skill Categorization Test\n")

    for skill in test_skills:
        category = SkillCategorizer.categorize(skill)
        print(f"  {skill:<30} → {category}")

    print("\n📊 Category Statistics:")
    stats = SkillCategorizer.get_category_stats(test_skills)
    for cat, count in sorted(stats.items()):
        print(f"  {cat:<20} {count} skills")
