#!/usr/bin/env python3
"""
Script to populate Neo4j with initial data for testing recommendations
"""

from app.database import get_database_manager
from app.util.env_config import Settings
from app.util.log import get_logger
from app.services.neo4j_user_service import Neo4jUserService
from app.services.neo4j_program_service import Neo4jProgramService

logger = get_logger(__name__)


def create_sample_data():
    """Create sample data in Neo4j for testing"""
    db_manager = get_database_manager()

    try:
        db_manager.initialize_all()

        with db_manager.neo4j.get_db_session() as session:
            # Create sample regions
            regions_data = [
                {"region_id": 1, "name": "United States", "code": "US"},
                {"region_id": 2, "name": "United Kingdom", "code": "UK"},
                {"region_id": 3, "name": "Canada", "code": "CA"},
                {"region_id": 4, "name": "Australia", "code": "AU"},
            ]

            for region in regions_data:
                region_query = """
                MERGE (r:Region {
                    region_id: $region_id,
                    name: $name,
                    code: $code
                })
                """
                session.run(region_query, region)

            # Create sample universities
            universities_data = [
                {
                    "university_id": 1,
                    "name": "MIT",
                    "city": "Cambridge",
                    "type": "Private",
                    "ranking_world": 1,
                    "ranking_national": 1,
                    "region_id": 1,
                },
                {
                    "university_id": 2,
                    "name": "Stanford University",
                    "city": "Stanford",
                    "type": "Private",
                    "ranking_world": 2,
                    "ranking_national": 2,
                    "region_id": 1,
                },
                {
                    "university_id": 3,
                    "name": "Harvard University",
                    "city": "Cambridge",
                    "type": "Private",
                    "ranking_world": 3,
                    "ranking_national": 3,
                    "region_id": 1,
                },
                {
                    "university_id": 4,
                    "name": "Oxford University",
                    "city": "Oxford",
                    "type": "Public",
                    "ranking_world": 4,
                    "ranking_national": 1,
                    "region_id": 2,
                },
            ]

            for university in universities_data:
                uni_query = """
                MERGE (u:University {
                    university_id: $university_id,
                    name: $name,
                    city: $city,
                    type: $type,
                    ranking_world: $ranking_world,
                    ranking_national: $ranking_national
                })
                
                WITH u
                MATCH (r:Region {region_id: $region_id})
                MERGE (u)-[:LOCATED_IN]->(r)
                """
                session.run(uni_query, university)

            # Create sample programs
            programs_data = [
                {
                    "program_id": 1,
                    "name": "Master of Science in Computer Science",
                    "degree_level": "master",
                    "field_of_study": "Computer Science",
                    "duration_years": 2.0,
                    "language": "English",
                    "tuition_fee": 55000.0,
                    "currency": "USD",
                    "is_active": True,
                    "university_id": 1,
                },
                {
                    "program_id": 2,
                    "name": "Bachelor of Science in Artificial Intelligence",
                    "degree_level": "bachelor",
                    "field_of_study": "Artificial Intelligence",
                    "duration_years": 4.0,
                    "language": "English",
                    "tuition_fee": 50000.0,
                    "currency": "USD",
                    "is_active": True,
                    "university_id": 2,
                },
                {
                    "program_id": 3,
                    "name": "PhD in Data Science",
                    "degree_level": "phd",
                    "field_of_study": "Data Science",
                    "duration_years": 5.0,
                    "language": "English",
                    "tuition_fee": 45000.0,
                    "currency": "USD",
                    "is_active": True,
                    "university_id": 3,
                },
                {
                    "program_id": 4,
                    "name": "Master of Engineering in Software Engineering",
                    "degree_level": "master",
                    "field_of_study": "Software Engineering",
                    "duration_years": 1.5,
                    "language": "English",
                    "tuition_fee": 40000.0,
                    "currency": "GBP",
                    "is_active": True,
                    "university_id": 4,
                },
            ]

            for program in programs_data:
                program_query = """
                MERGE (p:Program {
                    program_id: $program_id,
                    name: $name,
                    degree_level: $degree_level,
                    field_of_study: $field_of_study,
                    duration_years: $duration_years,
                    language: $language,
                    tuition_fee: $tuition_fee,
                    currency: $currency,
                    is_active: $is_active
                })
                
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
                """

                session.run(program_query, program)

            # Create sample requirements
            requirements_data = [
                {
                    "program_id": 1,
                    "requirement_type": "minimum_gpa",
                    "requirement_value": "3.5",
                    "test_type": None,
                    "is_mandatory": True,
                },
                {
                    "program_id": 1,
                    "requirement_type": "test_score",
                    "requirement_value": "320",
                    "test_type": "GRE",
                    "is_mandatory": True,
                },
                {
                    "program_id": 2,
                    "requirement_type": "minimum_gpa",
                    "requirement_value": "3.0",
                    "test_type": None,
                    "is_mandatory": True,
                },
                {
                    "program_id": 3,
                    "requirement_type": "test_score",
                    "requirement_value": "330",
                    "test_type": "GRE",
                    "is_mandatory": True,
                },
            ]

            for req in requirements_data:
                req_query = """
                MATCH (p:Program {program_id: $program_id})
                MERGE (req:Requirement {
                    requirement_type: $requirement_type,
                    requirement_value: $requirement_value,
                    test_type: $test_type,
                    is_mandatory: $is_mandatory
                })
                MERGE (p)-[:HAS_REQUIREMENT]->(req)
                
                // Create requirement type node
                WITH req
                MERGE (rt:RequirementType {type: $requirement_type})
                MERGE (req)-[:IS_TYPE]->(rt)
                """

                if req["test_type"]:
                    req_query += """
                    // Create test type node if exists
                    WITH req
                    MERGE (tt:TestType {name: $test_type})
                    MERGE (req)-[:REQUIRES_TEST]->(tt)
                    """

                session.run(req_query, req)

            # Create sample user interests for testing
            sample_interests = [
                {
                    "user_id": 1,
                    "interest_id": 1,
                    "field_of_study": "Computer Science",
                    "interest_level": "high",
                },
                {
                    "user_id": 1,
                    "interest_id": 2,
                    "field_of_study": "Artificial Intelligence",
                    "interest_level": "high",
                },
                {
                    "user_id": 2,
                    "interest_id": 3,
                    "field_of_study": "Data Science",
                    "interest_level": "medium",
                },
            ]

            for interest in sample_interests:
                interest_query = """
                MERGE (u:User {user_id: $user_id})
                MERGE (fs:FieldOfStudy {name: $field_of_study})
                MERGE (u)-[:INTERESTED_IN {
                    interest_id: $interest_id,
                    interest_level: $interest_level
                }]->(fs)
                """
                session.run(interest_query, interest)

            logger.info("Sample data created successfully in Neo4j")

    except Exception as e:
        logger.error(f"Failed to create sample data: {e}")
        raise
    finally:
        db_manager.close_all()


if __name__ == "__main__":
    create_sample_data()
