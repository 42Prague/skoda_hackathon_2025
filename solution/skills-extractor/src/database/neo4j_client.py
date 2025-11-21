"""Neo4j database client and connection management."""

import logging
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
from neo4j.exceptions import ServiceUnavailable, AuthError

from config.settings import settings

logger = logging.getLogger(__name__)


class Neo4jClient:
    """Neo4j database client for managing connections and queries."""

    def __init__(self):
        """Initialize the Neo4j client."""
        self.driver: Optional[AsyncDriver] = None
        self.uri = settings.neo4j_uri
        self.user = settings.neo4j_user
        self.password = settings.neo4j_password
        self.database = settings.neo4j_database

    async def connect(self) -> None:
        """Establish connection to Neo4j database."""
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_pool_size=50,
                connection_acquisition_timeout=30.0,
            )
            # Verify connectivity
            await self.driver.verify_connectivity()
            logger.info(f"Connected to Neo4j at {self.uri}")
        except (ServiceUnavailable, AuthError) as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    async def close(self) -> None:
        """Close the database connection."""
        if self.driver:
            await self.driver.close()
            logger.info("Neo4j connection closed")

    @asynccontextmanager
    async def session(self) -> AsyncSession:
        """Get a database session context manager."""
        if not self.driver:
            await self.connect()

        async with self.driver.session(database=self.database) as session:
            yield session

    async def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Execute a Cypher query and return results."""
        async with self.session() as session:
            result = await session.run(query, parameters or {})
            records = await result.data()
            return records

    async def execute_write(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Execute a write query (INSERT, UPDATE, DELETE)."""
        async with self.session() as session:
            await session.run(query, parameters or {})

    async def initialize_schema(self) -> None:
        """Initialize database schema with constraints and indexes."""
        logger.info("Initializing Neo4j schema...")

        queries = [
            # Constraints for uniqueness
            "CREATE CONSTRAINT job_id_unique IF NOT EXISTS FOR (j:Job) REQUIRE j.id IS UNIQUE",
            "CREATE CONSTRAINT skill_name_unique IF NOT EXISTS FOR (s:Skill) REQUIRE s.canonical_name IS UNIQUE",

            # Indexes for performance
            "CREATE INDEX job_title_index IF NOT EXISTS FOR (j:Job) ON (j.title)",
            "CREATE INDEX job_company_index IF NOT EXISTS FOR (j:Job) ON (j.company)",
            "CREATE INDEX skill_category_index IF NOT EXISTS FOR (s:Skill) ON (s.category)",

            # Full-text search indexes
            "CREATE FULLTEXT INDEX job_fulltext IF NOT EXISTS FOR (j:Job) ON EACH [j.title, j.description]",
            "CREATE FULLTEXT INDEX skill_fulltext IF NOT EXISTS FOR (s:Skill) ON EACH [s.canonical_name]",

            # Vector index for semantic search (Neo4j 5.x)
            """
            CALL db.index.vector.createNodeIndex(
                'skill_embeddings',
                'Skill',
                'embedding',
                768,
                'cosine'
            )
            """,
        ]

        for query in queries:
            try:
                await self.execute_write(query.strip())
                logger.info(f"Executed: {query[:50]}...")
            except Exception as e:
                # Some constraints/indexes might already exist
                if "already exists" in str(e).lower() or "equivalent" in str(e).lower():
                    logger.debug(f"Schema element already exists: {e}")
                else:
                    logger.warning(f"Error creating schema element: {e}")

        logger.info("Schema initialization complete")

    async def clear_database(self) -> None:
        """Clear all data from the database (use with caution!)."""
        logger.warning("Clearing all data from Neo4j database...")

        queries = [
            "MATCH (n) DETACH DELETE n",  # Delete all nodes and relationships
        ]

        for query in queries:
            await self.execute_write(query)

        logger.info("Database cleared successfully")

    async def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        queries = {
            "total_jobs": "MATCH (j:Job) RETURN count(j) as count",
            "total_skills": "MATCH (s:Skill) RETURN count(s) as count",
            "total_relationships": "MATCH ()-[r:REQUIRES]->() RETURN count(r) as count",
            "total_hierarchical": "MATCH ()-[r:PARENT_OF]->() RETURN count(r) as count",
        }

        stats = {}
        for key, query in queries.items():
            result = await self.execute_query(query)
            stats[key] = result[0]["count"] if result else 0

        # Get skill category breakdown
        category_query = """
        MATCH (s:Skill)
        RETURN s.category as category, count(s) as count
        """
        category_result = await self.execute_query(category_query)
        stats["skill_categories"] = {
            row["category"]: row["count"] for row in category_result
        }

        # Calculate average skills per job
        if stats["total_jobs"] > 0:
            stats["avg_skills_per_job"] = stats["total_relationships"] / stats["total_jobs"]
        else:
            stats["avg_skills_per_job"] = 0.0

        return stats


# Global client instance
neo4j_client = Neo4jClient()
