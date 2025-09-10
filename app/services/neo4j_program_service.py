from typing import Optional, List, Dict, Any
from datetime import datetime
from neo4j import Session
from app.database import get_database_manager
from app.models import Program, University, Region, ProgramRequirement
from app.util.log import get_logger

logger = get_logger(__name__)


class Neo4jProgramService:
    """Service for managing program, university, and region data in Neo4j"""

    def __init__(self):
        self.db_manager = get_database_manager()

    def create_region_node(self, region: Region) -> bool:
        """Create region node in Neo4j"""
        try:
            with self.db_manager.neo4j.get_db_session() as session:
                query = """
                MERGE (r:Region {
                    region_id: $region_id,
                    name: $name,
                    code: $code
                })
                SET r.updated_at = $updated_at
                RETURN r
                """

                parameters = {
                    "region_id": region.id,
                    "name": region.name,
                    "code": region.code,
                    "updated_at": datetime.utcnow().isoformat(),
                }

                session.run(query, parameters)
                logger.info(f"Region node created/updated in Neo4j: {region.name}")
                return True

        except Exception as e:
            logger.error(f"Failed to create region node in Neo4j: {e}")
            return False

    def create_university_node(self, university: University) -> bool:
        """Create university node and relationships in Neo4j"""
        try:
            with self.db_manager.neo4j.get_db_session() as session:
                # Create university node - only use university_id for MERGE, then SET all properties
                query = """
                MERGE (u:University {university_id: $university_id})
                SET u.name = $name,
                    u.city = $city,
                    u.established_year = $established_year,
                    u.type = $type,
                    u.website = $website,
                    u.description = $description,
                    u.ranking_world = $ranking_world,
                    u.ranking_national = $ranking_national,
                    u.created_at = $created_at,
                    u.updated_at = $updated_at
                
                // Create relationship with region
                WITH u
                MATCH (r:Region {region_id: $region_id})
                MERGE (u)-[:LOCATED_IN]->(r)
                
                RETURN u
                """

                parameters = {
                    "university_id": university.id,
                    "name": university.name,
                    "city": university.city,
                    "established_year": university.established_year,
                    "type": university.type,
                    "website": university.website,
                    "description": university.description,
                    "ranking_world": university.ranking_world,
                    "ranking_national": university.ranking_national,
                    "region_id": university.region_id,
                    "created_at": (
                        university.created_at.isoformat()
                        if university.created_at
                        else None
                    ),
                    "updated_at": datetime.utcnow().isoformat(),
                }

                session.run(query, parameters)
                logger.info(
                    f"University node created/updated in Neo4j: {university.name}"
                )
                return True

        except Exception as e:
            logger.error(f"Failed to create university node in Neo4j: {e}")
            return False

    def create_program_node(self, program: Program) -> bool:
        """Create program node and relationships in Neo4j"""
        try:
            with self.db_manager.neo4j.get_db_session() as session:
                # Create program node - only use program_id for MERGE, then SET all properties
                query = """
                MERGE (p:Program {program_id: $program_id})
                SET p.name = $name,
                    p.degree_level = $degree_level,
                    p.field_of_study = $field_of_study,
                    p.duration_years = $duration_years,
                    p.language = $language,
                    p.tuition_fee = $tuition_fee,
                    p.currency = $currency,
                    p.application_deadline = $application_deadline,
                    p.start_date = $start_date,
                    p.description = $description,
                    p.is_active = $is_active,
                    p.updated_at = $updated_at
                
                // Create relationships
                WITH p
                MATCH (u:University {university_id: $university_id})
                MERGE (p)-[:OFFERED_BY]->(u)
                
                // Create field of study node and relationship
                WITH p
                MERGE (fs:FieldOfStudy {name: $field_of_study})
                MERGE (p)-[:BELONGS_TO_FIELD]->(fs)
                
                // Create degree level node and relationship
                WITH p
                MERGE (dl:DegreeLevel {level: $degree_level})
                MERGE (p)-[:HAS_DEGREE_LEVEL]->(dl)
                
                // Create language node and relationship
                WITH p
                MERGE (lang:Language {name: $language})
                MERGE (p)-[:TAUGHT_IN]->(lang)
                
                RETURN p
                """

                parameters = {
                    "program_id": program.id,
                    "name": program.name,
                    "degree_level": program.degree_level.value,
                    "field_of_study": program.field_of_study,
                    "duration_years": (
                        float(program.duration_years)
                        if program.duration_years
                        else None
                    ),
                    "language": program.language,
                    "tuition_fee": (
                        float(program.tuition_fee) if program.tuition_fee else None
                    ),
                    "currency": program.currency,
                    "application_deadline": (
                        program.application_deadline.isoformat()
                        if program.application_deadline
                        else None
                    ),
                    "start_date": (
                        program.start_date.isoformat() if program.start_date else None
                    ),
                    "description": program.description,
                    "is_active": program.is_active,
                    "university_id": program.university_id,
                    "updated_at": datetime.utcnow().isoformat(),
                }

                session.run(query, parameters)

                # Add program requirements
                if program.requirements:
                    self._create_program_requirements(session, program)

                logger.info(f"Program node created/updated in Neo4j: {program.name}")
                return True

        except Exception as e:
            logger.error(f"Failed to create program node in Neo4j: {e}")
            return False

    def _create_program_requirements(self, session: Session, program: Program):
        """Create program requirements nodes and relationships"""
        for requirement in program.requirements:
            req_query = """
            MATCH (p:Program {program_id: $program_id})
            MERGE (req:Requirement {requirement_id: $requirement_id})
            SET req.requirement_type = $requirement_type,
                req.requirement_value = $requirement_value,
                req.test_type = $test_type,
                req.is_mandatory = $is_mandatory,
                req.description = $description
            MERGE (p)-[:HAS_REQUIREMENT]->(req)
            
            // Create requirement type node
            WITH req
            MERGE (rt:RequirementType {type: $requirement_type})
            MERGE (req)-[:IS_TYPE]->(rt)
            
            // Create test type node if exists
            WITH req
            CASE 
                WHEN $test_type IS NOT NULL THEN
                    MERGE (tt:TestType {name: $test_type})
                    MERGE (req)-[:REQUIRES_TEST]->(tt)
                ELSE
                    RETURN req
            END
            """

            parameters = {
                "program_id": program.id,
                "requirement_id": requirement.id,
                "requirement_type": requirement.requirement_type,
                "requirement_value": requirement.requirement_value,
                "test_type": requirement.test_type,
                "is_mandatory": requirement.is_mandatory,
                "description": requirement.description,
            }

            session.run(req_query, parameters)

    def update_region_node(self, region: Region) -> bool:
        """Update region node in Neo4j"""
        try:
            with self.db_manager.neo4j.get_db_session() as session:
                query = """
                MATCH (r:Region {region_id: $region_id})
                SET r.name = $name,
                    r.code = $code,
                    r.updated_at = $updated_at
                RETURN r
                """

                parameters = {
                    "region_id": region.id,
                    "name": region.name,
                    "code": region.code,
                    "updated_at": datetime.utcnow().isoformat(),
                }

                result = session.run(query, parameters)
                if result.single():
                    logger.info(f"Region node updated in Neo4j: {region.name}")
                    return True
                else:
                    logger.warning(f"Region node not found in Neo4j: {region.name}")
                    return False

        except Exception as e:
            logger.error(f"Failed to update region node in Neo4j: {e}")
            return False

    def update_university_node(self, university: University) -> bool:
        """Update university node in Neo4j"""
        try:
            with self.db_manager.neo4j.get_db_session() as session:
                query = """
                MATCH (u:University {university_id: $university_id})
                SET u.name = $name,
                    u.city = $city,
                    u.established_year = $established_year,
                    u.type = $type,
                    u.website = $website,
                    u.description = $description,
                    u.ranking_world = $ranking_world,
                    u.ranking_national = $ranking_national,
                    u.updated_at = $updated_at
                
                // Update region relationship
                WITH u
                MATCH (u)-[old_rel:LOCATED_IN]->()
                DELETE old_rel
                
                WITH u
                MATCH (r:Region {region_id: $region_id})
                MERGE (u)-[:LOCATED_IN]->(r)
                
                RETURN u
                """

                parameters = {
                    "university_id": university.id,
                    "name": university.name,
                    "city": university.city,
                    "established_year": university.established_year,
                    "type": university.type,
                    "website": university.website,
                    "description": university.description,
                    "ranking_world": university.ranking_world,
                    "ranking_national": university.ranking_national,
                    "region_id": university.region_id,
                    "updated_at": datetime.utcnow().isoformat(),
                }

                result = session.run(query, parameters)
                if result.single():
                    logger.info(f"University node updated in Neo4j: {university.name}")
                    return True
                else:
                    logger.warning(
                        f"University node not found in Neo4j: {university.name}"
                    )
                    return False

        except Exception as e:
            logger.error(f"Failed to update university node in Neo4j: {e}")
            return False

    def update_program_node(self, program: Program) -> bool:
        """Update program node in Neo4j"""
        try:
            with self.db_manager.neo4j.get_db_session() as session:
                query = """
                MATCH (p:Program {program_id: $program_id})
                SET p.name = $name,
                    p.degree_level = $degree_level,
                    p.field_of_study = $field_of_study,
                    p.duration_years = $duration_years,
                    p.language = $language,
                    p.tuition_fee = $tuition_fee,
                    p.currency = $currency,
                    p.application_deadline = $application_deadline,
                    p.start_date = $start_date,
                    p.description = $description,
                    p.is_active = $is_active,
                    p.updated_at = $updated_at
                
                // Update university relationship
                WITH p
                MATCH (p)-[old_rel:OFFERED_BY]->()
                DELETE old_rel
                
                WITH p
                MATCH (u:University {university_id: $university_id})
                MERGE (p)-[:OFFERED_BY]->(u)
                
                // Update field of study relationship
                WITH p
                MATCH (p)-[old_fs:BELONGS_TO_FIELD]->()
                DELETE old_fs
                
                WITH p
                MERGE (fs:FieldOfStudy {name: $field_of_study})
                MERGE (p)-[:BELONGS_TO_FIELD]->(fs)
                
                // Update degree level relationship
                WITH p
                MATCH (p)-[old_dl:HAS_DEGREE_LEVEL]->()
                DELETE old_dl
                
                WITH p
                MERGE (dl:DegreeLevel {level: $degree_level})
                MERGE (p)-[:HAS_DEGREE_LEVEL]->(dl)
                
                // Update language relationship
                WITH p
                MATCH (p)-[old_lang:TAUGHT_IN]->()
                DELETE old_lang
                
                WITH p
                MERGE (lang:Language {name: $language})
                MERGE (p)-[:TAUGHT_IN]->(lang)
                
                RETURN p
                """

                parameters = {
                    "program_id": program.id,
                    "name": program.name,
                    "degree_level": program.degree_level.value,
                    "field_of_study": program.field_of_study,
                    "duration_years": (
                        float(program.duration_years)
                        if program.duration_years
                        else None
                    ),
                    "language": program.language,
                    "tuition_fee": (
                        float(program.tuition_fee) if program.tuition_fee else None
                    ),
                    "currency": program.currency,
                    "application_deadline": (
                        program.application_deadline.isoformat()
                        if program.application_deadline
                        else None
                    ),
                    "start_date": (
                        program.start_date.isoformat() if program.start_date else None
                    ),
                    "description": program.description,
                    "is_active": program.is_active,
                    "university_id": program.university_id,
                    "updated_at": datetime.utcnow().isoformat(),
                }

                result = session.run(query, parameters)
                if result.single():
                    logger.info(f"Program node updated in Neo4j: {program.name}")
                    return True
                else:
                    logger.warning(f"Program node not found in Neo4j: {program.name}")
                    return False

        except Exception as e:
            logger.error(f"Failed to update program node in Neo4j: {e}")
            return False

    def delete_region_node(self, region_id: int) -> bool:
        """Delete region node from Neo4j"""
        try:
            with self.db_manager.neo4j.get_db_session() as session:
                query = """
                MATCH (r:Region {region_id: $region_id})
                DETACH DELETE r
                """

                session.run(query, {"region_id": region_id})
                logger.info(f"Region node deleted from Neo4j: {region_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to delete region node from Neo4j: {e}")
            return False

    def delete_university_node(self, university_id: int) -> bool:
        """Delete university node from Neo4j"""
        try:
            with self.db_manager.neo4j.get_db_session() as session:
                query = """
                MATCH (u:University {university_id: $university_id})
                DETACH DELETE u
                """

                session.run(query, {"university_id": university_id})
                logger.info(f"University node deleted from Neo4j: {university_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to delete university node from Neo4j: {e}")
            return False

    def delete_program_node(self, program_id: int) -> bool:
        """Delete program node from Neo4j (or mark as inactive)"""
        try:
            with self.db_manager.neo4j.get_db_session() as session:
                # For soft delete, just mark as inactive
                query = """
                MATCH (p:Program {program_id: $program_id})
                SET p.is_active = false,
                    p.updated_at = $updated_at
                RETURN p
                """

                parameters = {
                    "program_id": program_id,
                    "updated_at": datetime.utcnow().isoformat(),
                }

                result = session.run(query, parameters)
                if result.single():
                    logger.info(f"Program node soft deleted in Neo4j: {program_id}")
                    return True
                else:
                    logger.warning(f"Program node not found in Neo4j: {program_id}")
                    return False

        except Exception as e:
            logger.error(f"Failed to delete program node from Neo4j: {e}")
            return False

    def get_program_recommendations_by_field(
        self, field_of_study: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get program recommendations based on field of study"""
        try:
            with self.db_manager.neo4j.get_db_session() as session:
                query = """
                MATCH (p:Program)-[:BELONGS_TO_FIELD]->(fs:FieldOfStudy {name: $field_of_study})
                MATCH (p)-[:OFFERED_BY]->(u:University)
                WHERE p.is_active = true
                RETURN p.program_id as program_id,
                       p.name as program_name,
                       p.degree_level as degree_level,
                       p.tuition_fee as tuition_fee,
                       p.currency as currency,
                       u.name as university_name,
                       u.ranking_world as university_ranking
                ORDER BY u.ranking_world ASC
                LIMIT $limit
                """

                result = session.run(
                    query, {"field_of_study": field_of_study, "limit": limit}
                )
                recommendations = []

                for record in result:
                    recommendations.append(
                        {
                            "program_id": record["program_id"],
                            "program_name": record["program_name"],
                            "degree_level": record["degree_level"],
                            "tuition_fee": record["tuition_fee"],
                            "currency": record["currency"],
                            "university_name": record["university_name"],
                            "university_ranking": record["university_ranking"],
                        }
                    )

                return recommendations

        except Exception as e:
            logger.error(f"Failed to get program recommendations from Neo4j: {e}")
            return []

    def get_universities_by_region(self, region_id: int) -> List[Dict[str, Any]]:
        """Get universities by region from Neo4j"""
        try:
            with self.db_manager.neo4j.get_db_session() as session:
                query = """
                MATCH (u:University)-[:LOCATED_IN]->(r:Region {region_id: $region_id})
                RETURN u.university_id as university_id,
                       u.name as university_name,
                       u.city as city,
                       u.type as type,
                       u.ranking_world as ranking_world,
                       u.ranking_national as ranking_national
                ORDER BY u.ranking_world ASC
                """

                result = session.run(query, {"region_id": region_id})
                universities = []

                for record in result:
                    universities.append(
                        {
                            "university_id": record["university_id"],
                            "university_name": record["university_name"],
                            "city": record["city"],
                            "type": record["type"],
                            "ranking_world": record["ranking_world"],
                            "ranking_national": record["ranking_national"],
                        }
                    )

                return universities

        except Exception as e:
            logger.error(f"Failed to get universities by region from Neo4j: {e}")
            return []
