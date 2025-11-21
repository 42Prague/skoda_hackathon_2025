"""Database operations for jobs and skills."""

import logging
from typing import List, Dict, Any, Optional, Set

from src.models import Job, Skill, JobSkillRelationship, NormalizedSkill
from .neo4j_client import neo4j_client

logger = logging.getLogger(__name__)


async def create_job(job: Job) -> None:
    """Create a job node in the database."""
    query = """
    MERGE (j:Job {id: $id})
    SET j.title = $title,
        j.description = $description,
        j.company = $company,
        j.location = $location,
        j.salary = $salary,
        j.updated_at = datetime()
    """
    await neo4j_client.execute_write(
        query,
        {
            "id": job.id,
            "title": job.title,
            "description": job.description,
            "company": job.company,
            "location": job.location,
            "salary": job.salary,
        },
    )


async def create_jobs_bulk(jobs: List[Job]) -> None:
    """Create multiple job nodes in bulk."""
    query = """
    UNWIND $jobs as job
    MERGE (j:Job {id: job.id})
    SET j.title = job.title,
        j.description = job.description,
        j.company = job.company,
        j.location = job.location,
        j.salary = job.salary,
        j.updated_at = datetime()
    """
    jobs_data = [
        {
            "id": job.id,
            "title": job.title,
            "description": job.description,
            "company": job.company,
            "location": job.location,
            "salary": job.salary,
        }
        for job in jobs
    ]
    await neo4j_client.execute_write(query, {"jobs": jobs_data})
    logger.info(f"Created {len(jobs)} jobs in database")


async def create_skill(skill: NormalizedSkill) -> None:
    """Create a skill node in the database."""
    query = """
    MERGE (s:Skill {canonical_name: $canonical_name})
    SET s.category = $category,
        s.aliases = $aliases,
        s.embedding = $embedding,
        s.updated_at = datetime()
    """
    await neo4j_client.execute_write(
        query,
        {
            "canonical_name": skill.canonical_name,
            "category": skill.category.value,
            "aliases": skill.aliases,
            "embedding": skill.embedding,
        },
    )


async def create_skills_bulk(skills: List[NormalizedSkill]) -> None:
    """Create multiple skill nodes in bulk."""
    query = """
    UNWIND $skills as skill
    MERGE (s:Skill {canonical_name: skill.canonical_name})
    SET s.category = skill.category,
        s.aliases = skill.aliases,
        s.embedding = skill.embedding,
        s.updated_at = datetime()
    """
    skills_data = [
        {
            "canonical_name": skill.canonical_name,
            "category": skill.category.value,
            "aliases": skill.aliases,
            "embedding": skill.embedding,
        }
        for skill in skills
    ]
    await neo4j_client.execute_write(query, {"skills": skills_data})
    logger.info(f"Created {len(skills)} skills in database")


async def create_job_skill_relationship(relationship: JobSkillRelationship) -> None:
    """Create a REQUIRES relationship between job and skill."""
    query = """
    MATCH (j:Job {id: $job_id})
    MATCH (s:Skill {canonical_name: $skill_name})
    MERGE (j)-[r:REQUIRES]->(s)
    SET r.confidence = $confidence,
        r.required = $required,
        r.level = $level
    """
    await neo4j_client.execute_write(
        query,
        {
            "job_id": relationship.job_id,
            "skill_name": relationship.skill_name,
            "confidence": relationship.confidence,
            "required": relationship.required,
            "level": relationship.level.value if relationship.level else None,
        },
    )


async def create_job_skill_relationships_bulk(
    relationships: List[JobSkillRelationship]
) -> None:
    """Create multiple job-skill relationships in bulk."""
    query = """
    UNWIND $relationships as rel
    MATCH (j:Job {id: rel.job_id})
    MATCH (s:Skill {canonical_name: rel.skill_name})
    MERGE (j)-[r:REQUIRES]->(s)
    SET r.confidence = rel.confidence,
        r.required = rel.required,
        r.level = rel.level
    """
    rel_data = [
        {
            "job_id": rel.job_id,
            "skill_name": rel.skill_name,
            "confidence": rel.confidence,
            "required": rel.required,
            "level": rel.level.value if rel.level else None,
        }
        for rel in relationships
    ]
    await neo4j_client.execute_write(query, {"relationships": rel_data})
    logger.info(f"Created {len(relationships)} job-skill relationships")


async def create_skill_hierarchy(parent_name: str, child_name: str) -> None:
    """Create a PARENT_OF relationship between skills."""
    query = """
    MATCH (parent:Skill {canonical_name: $parent_name})
    MATCH (child:Skill {canonical_name: $child_name})
    MERGE (parent)-[r:PARENT_OF]->(child)
    """
    await neo4j_client.execute_write(
        query,
        {"parent_name": parent_name, "child_name": child_name},
    )


async def create_skill_hierarchies_bulk(hierarchies: List[tuple[str, str]]) -> None:
    """Create multiple skill hierarchy relationships in bulk."""
    query = """
    UNWIND $hierarchies as hierarchy
    MATCH (parent:Skill {canonical_name: hierarchy.parent})
    MATCH (child:Skill {canonical_name: hierarchy.child})
    MERGE (parent)-[r:PARENT_OF]->(child)
    """
    hierarchy_data = [
        {"parent": parent, "child": child} for parent, child in hierarchies
    ]
    await neo4j_client.execute_write(query, {"hierarchies": hierarchy_data})
    logger.info(f"Created {len(hierarchies)} skill hierarchy relationships")


async def get_skill_by_name(canonical_name: str) -> Optional[Skill]:
    """Get a skill by its canonical name."""
    query = """
    MATCH (s:Skill {canonical_name: $canonical_name})
    OPTIONAL MATCH (s)-[:PARENT_OF]->(child:Skill)
    OPTIONAL MATCH (parent:Skill)-[:PARENT_OF]->(s)
    RETURN s,
           collect(DISTINCT child.canonical_name) as children,
           collect(DISTINCT parent.canonical_name) as parents
    """
    result = await neo4j_client.execute_query(
        query, {"canonical_name": canonical_name}
    )

    if not result:
        return None

    row = result[0]
    skill_data = row["s"]

    return Skill(
        canonical_name=skill_data["canonical_name"],
        category=skill_data["category"],
        aliases=skill_data.get("aliases", []),
        embedding=skill_data.get("embedding"),
        parent_skills=[p for p in row["parents"] if p],
        child_skills=[c for c in row["children"] if c],
    )


async def get_all_skills() -> List[Skill]:
    """Get all skills from the database."""
    query = """
    MATCH (s:Skill)
    OPTIONAL MATCH (s)-[:PARENT_OF]->(child:Skill)
    OPTIONAL MATCH (parent:Skill)-[:PARENT_OF]->(s)
    RETURN s,
           collect(DISTINCT child.canonical_name) as children,
           collect(DISTINCT parent.canonical_name) as parents
    """
    results = await neo4j_client.execute_query(query)

    skills = []
    for row in results:
        skill_data = row["s"]
        skills.append(
            Skill(
                canonical_name=skill_data["canonical_name"],
                category=skill_data["category"],
                aliases=skill_data.get("aliases", []),
                embedding=skill_data.get("embedding"),
                parent_skills=[p for p in row["parents"] if p],
                child_skills=[c for c in row["children"] if c],
            )
        )

    return skills


async def find_similar_skills(
    embedding: List[float], limit: int = 5, threshold: float = 0.85
) -> List[Dict[str, Any]]:
    """Find similar skills using vector search."""
    query = """
    CALL db.index.vector.queryNodes('skill_embeddings', $limit, $embedding)
    YIELD node, score
    WHERE score >= $threshold
    RETURN node.canonical_name as canonical_name,
           node.category as category,
           score as similarity
    ORDER BY score DESC
    """
    results = await neo4j_client.execute_query(
        query,
        {"embedding": embedding, "limit": limit, "threshold": threshold},
    )

    return results


async def get_job_by_id(job_id: str) -> Optional[Job]:
    """Get a job by its ID."""
    query = """
    MATCH (j:Job {id: $job_id})
    RETURN j
    """
    result = await neo4j_client.execute_query(query, {"job_id": job_id})

    if not result:
        return None

    job_data = result[0]["j"]
    return Job(
        id=job_data["id"],
        title=job_data["title"],
        description=job_data["description"],
        company=job_data.get("company"),
        location=job_data.get("location"),
        salary=job_data.get("salary"),
    )


async def get_jobs_by_skills(
    skill_names: List[str],
    match_all: bool = False,
    include_parents: bool = True,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """Find jobs that require the specified skills."""
    if include_parents:
        # Also match jobs requiring parent skills (if you have Django, you qualify for Python jobs)
        query = """
        MATCH (s:Skill)
        WHERE s.canonical_name IN $skill_names
        OPTIONAL MATCH (parent:Skill)-[:PARENT_OF*]->(s)
        WITH collect(DISTINCT s.canonical_name) + collect(DISTINCT parent.canonical_name) as all_skills

        MATCH (j:Job)-[r:REQUIRES]->(skill:Skill)
        WHERE skill.canonical_name IN all_skills

        WITH j, collect(DISTINCT skill.canonical_name) as matched_skills, count(DISTINCT skill) as match_count
        MATCH (j)-[:REQUIRES]->(s:Skill)
        WITH j, matched_skills, match_count, count(s) as total_skills
        """

        if match_all:
            query += "WHERE match_count >= $min_matches "

        query += """
        RETURN j as job,
               matched_skills,
               match_count,
               CASE WHEN total_skills > 0 THEN toFloat(match_count) / total_skills ELSE 0.0 END as coverage
        ORDER BY match_count DESC, coverage DESC
        LIMIT $limit
        """

        params = {
            "skill_names": skill_names,
            "limit": limit,
        }
        if match_all:
            params["min_matches"] = len(skill_names)

    else:
        # Simple match without parent skills
        query = """
        MATCH (j:Job)-[r:REQUIRES]->(s:Skill)
        WHERE s.canonical_name IN $skill_names
        WITH j, collect(DISTINCT s.canonical_name) as matched_skills, count(DISTINCT s) as match_count
        MATCH (j)-[:REQUIRES]->(all_skills:Skill)
        WITH j, matched_skills, match_count, count(all_skills) as total_skills
        """

        if match_all:
            query += "WHERE match_count >= $min_matches "

        query += """
        RETURN j as job,
               matched_skills,
               match_count,
               toFloat(match_count) / total_skills as coverage
        ORDER BY match_count DESC, coverage DESC
        LIMIT $limit
        """

        params = {
            "skill_names": skill_names,
            "limit": limit,
        }
        if match_all:
            params["min_matches"] = len(skill_names)

    return await neo4j_client.execute_query(query, params)


async def get_candidate_job_titles(job_title: str) -> List[str]:
    """Get candidate job titles from full-text search.

    Args:
        job_title: Job title search query

    Returns:
        List of unique job titles that matched the search
    """
    query = """
    CALL db.index.fulltext.queryNodes('job_fulltext', $job_title)
    YIELD node as j, score
    WITH j.title as title, max(score) as max_score
    RETURN DISTINCT title, max_score
    ORDER BY max_score DESC
    """
    results = await neo4j_client.execute_query(query, {"job_title": job_title})
    return [row["title"] for row in results]


async def get_skills_by_job_titles(
    job_titles: List[str], include_children: bool = True
) -> List[Dict[str, Any]]:
    """Find skills required by specific job titles.

    Args:
        job_titles: List of exact job titles to query
        include_children: Include child skills in hierarchy

    Returns:
        List of skills with metadata
    """
    if not job_titles:
        return []

    if include_children:
        query = """
        MATCH (j:Job)-[r:REQUIRES]->(s:Skill)
        WHERE j.title IN $job_titles
        OPTIONAL MATCH (s)-[:PARENT_OF*]->(child:Skill)

        WITH s, r, collect(DISTINCT child.canonical_name) as children
        RETURN s.canonical_name as canonical_name,
               s.category as category,
               s.aliases as aliases,
               children,
               avg(r.confidence) as avg_confidence,
               count(*) as frequency
        ORDER BY frequency DESC, avg_confidence DESC
        """
    else:
        query = """
        MATCH (j:Job)-[r:REQUIRES]->(s:Skill)
        WHERE j.title IN $job_titles

        WITH s, r
        RETURN s.canonical_name as canonical_name,
               s.category as category,
               s.aliases as aliases,
               [] as children,
               avg(r.confidence) as avg_confidence,
               count(*) as frequency
        ORDER BY frequency DESC, avg_confidence DESC
        """

    return await neo4j_client.execute_query(query, {"job_titles": job_titles})


async def get_skills_by_job_title(
    job_title: str, include_children: bool = True
) -> List[Dict[str, Any]]:
    """Find skills required by jobs with matching title (legacy method without LLM filtering)."""
    if include_children:
        query = """
        CALL db.index.fulltext.queryNodes('job_fulltext', $job_title)
        YIELD node as j, score
        MATCH (j)-[r:REQUIRES]->(s:Skill)
        OPTIONAL MATCH (s)-[:PARENT_OF*]->(child:Skill)

        WITH s, collect(DISTINCT child.canonical_name) as children,
             avg(score) as relevance_score,
             avg(r.confidence) as avg_confidence,
             count(*) as frequency
        RETURN s.canonical_name as canonical_name,
               s.category as category,
               s.aliases as aliases,
               children,
               avg_confidence,
               frequency,
               relevance_score
        ORDER BY frequency DESC, avg_confidence DESC
        """
    else:
        query = """
        CALL db.index.fulltext.queryNodes('job_fulltext', $job_title)
        YIELD node as j, score
        MATCH (j)-[r:REQUIRES]->(s:Skill)

        WITH s, avg(score) as relevance_score,
             avg(r.confidence) as avg_confidence,
             count(*) as frequency
        RETURN s.canonical_name as canonical_name,
               s.category as category,
               s.aliases as aliases,
               [] as children,
               avg_confidence,
               frequency,
               relevance_score
        ORDER BY frequency DESC, avg_confidence DESC
        """

    return await neo4j_client.execute_query(query, {"job_title": job_title})


async def search_skills(
    query: str,
    top_k: int = 10,
    min_similarity: float = 0.7,
    include_exact: bool = True,
    include_aliases: bool = True,
    include_semantic: bool = True,
) -> List[Dict[str, Any]]:
    """Search for skills by name with exact, alias, and semantic matching."""
    results = []
    seen_names: Set[str] = set()

    # 1. Exact match
    if include_exact:
        exact_query = """
        MATCH (s:Skill)
        WHERE toLower(s.canonical_name) = toLower($query)
        OPTIONAL MATCH (s)-[:PARENT_OF]->(child:Skill)
        OPTIONAL MATCH (parent:Skill)-[:PARENT_OF]->(s)
        RETURN s.canonical_name as canonical_name,
               s.category as category,
               s.aliases as aliases,
               collect(DISTINCT parent.canonical_name) as parent_skills,
               collect(DISTINCT child.canonical_name) as child_skills,
               'exact' as match_type,
               1.0 as similarity
        """
        exact_results = await neo4j_client.execute_query(exact_query, {"query": query})
        for row in exact_results:
            if row["canonical_name"] not in seen_names:
                seen_names.add(row["canonical_name"])
                results.append(row)

    # 2. Alias match
    if include_aliases:
        alias_query = """
        MATCH (s:Skill)
        WHERE any(alias IN s.aliases WHERE toLower(alias) = toLower($query))
        OPTIONAL MATCH (s)-[:PARENT_OF]->(child:Skill)
        OPTIONAL MATCH (parent:Skill)-[:PARENT_OF]->(s)
        RETURN s.canonical_name as canonical_name,
               s.category as category,
               s.aliases as aliases,
               collect(DISTINCT parent.canonical_name) as parent_skills,
               collect(DISTINCT child.canonical_name) as child_skills,
               'alias' as match_type,
               0.95 as similarity
        """
        alias_results = await neo4j_client.execute_query(alias_query, {"query": query})
        for row in alias_results:
            if row["canonical_name"] not in seen_names:
                seen_names.add(row["canonical_name"])
                results.append(row)

    # 3. Semantic search (if we have embeddings)
    if include_semantic and len(results) < top_k:
        try:
            from sentence_transformers import SentenceTransformer
            from config.settings import settings

            # Load embedding model
            model = SentenceTransformer(settings.embedding_model)

            # Get embedding for query
            query_embedding = model.encode([query])[0].tolist()

            # Find similar skills
            semantic_query = """
            CALL db.index.vector.queryNodes('skill_embeddings', $top_k, $embedding)
            YIELD node, score
            WHERE score >= $threshold
            OPTIONAL MATCH (node)-[:PARENT_OF]->(child:Skill)
            OPTIONAL MATCH (parent:Skill)-[:PARENT_OF]->(node)
            RETURN node.canonical_name as canonical_name,
                   node.category as category,
                   node.aliases as aliases,
                   collect(DISTINCT parent.canonical_name) as parent_skills,
                   collect(DISTINCT child.canonical_name) as child_skills,
                   'semantic' as match_type,
                   score as similarity
            ORDER BY score DESC
            """
            semantic_results = await neo4j_client.execute_query(
                semantic_query,
                {
                    "embedding": query_embedding,
                    "threshold": min_similarity,
                    "top_k": top_k * 2,  # Get more to filter out duplicates
                },
            )

            for row in semantic_results:
                if row["canonical_name"] not in seen_names and len(results) < top_k:
                    seen_names.add(row["canonical_name"])
                    results.append(row)
        except Exception as e:
            logger.warning(f"Semantic search failed: {e}")

    # Limit to top_k and clean up child/parent lists
    results = results[:top_k]
    for result in results:
        # Filter out None values from lists
        result["parent_skills"] = [p for p in result["parent_skills"] if p]
        result["child_skills"] = [c for c in result["child_skills"] if c]

    return results


async def search_jobs_fulltext(
    query: str, top_k: int = 10, search_in_description: bool = False
) -> List[Dict[str, Any]]:
    """Search for jobs using full-text search on title and optionally description."""
    if search_in_description:
        # Search in both title and description
        cypher_query = """
        CALL db.index.fulltext.queryNodes('job_fulltext', $query)
        YIELD node as j, score
        RETURN j as job,
               score
        ORDER BY score DESC
        LIMIT $limit
        """
    else:
        # Search only in title (more precise)
        cypher_query = """
        MATCH (j:Job)
        WHERE toLower(j.title) CONTAINS toLower($query)
        WITH j, 1.0 as score
        RETURN j as job,
               score
        ORDER BY j.title
        LIMIT $limit
        """

    results = await neo4j_client.execute_query(
        cypher_query, {"query": query, "limit": top_k}
    )

    return results
