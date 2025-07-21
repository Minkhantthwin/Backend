from typing import Optional, List, Dict, Any
from datetime import datetime
from neo4j import Session
from app.database import get_database_manager
from app.models import User, UserQualification, UserInterest, UserTestScore
from app.util.log import get_logger

logger = get_logger(__name__)


class Neo4jUserService:
    """Service for managing user data and relationships in Neo4j"""

    def __init__(self):
        self.db_manager = get_database_manager()

    def create_user_node(self, user: User) -> bool:
        """Create user node in Neo4j with all related data"""
        try:
            with self.db_manager.neo4j.get_db_session() as session:
                # Create user node
                self._create_user_node_transaction(session, user)

                # Create qualification nodes and relationships
                if user.qualifications:
                    self._create_qualification_relationships(session, user)

                # Create interest nodes and relationships
                if user.interests:
                    self._create_interest_relationships(session, user)

                # Create test score nodes and relationships
                if user.test_scores:
                    self._create_test_score_relationships(session, user)

                logger.info(f"User node created successfully in Neo4j: {user.email}")
                return True

        except Exception as e:
            logger.error(f"Failed to create user node in Neo4j: {e}")
            return False

    def _create_user_node_transaction(self, session: Session, user: User):
        """Create the main user node"""
        query = """
        CREATE (u:User {
            user_id: $user_id,
            email: $email,
            first_name: $first_name,
            last_name: $last_name,
            date_of_birth: $date_of_birth,
            nationality: $nationality,
            phone: $phone,
            created_at: $created_at,
            updated_at: $updated_at
        })
        RETURN u
        """

        parameters = {
            "user_id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "date_of_birth": (
                user.date_of_birth.isoformat() if user.date_of_birth else None
            ),
            "nationality": user.nationality,
            "phone": user.phone,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        }

        session.run(query, parameters)

    def _create_qualification_relationships(self, session: Session, user: User):
        """Create qualification nodes and relationships"""
        for qualification in user.qualifications:
            # Create or match qualification type node
            qual_query = """
            MERGE (qt:QualificationType {type: $qual_type})
            MERGE (fs:FieldOfStudy {name: $field_of_study})
            MERGE (inst:Institution {name: $institution_name, country: $country})
            
            MATCH (u:User {user_id: $user_id})
            CREATE (u)-[:HAS_QUALIFICATION {
                qualification_id: $qualification_id,
                degree_name: $degree_name,
                grade_point: $grade_point,
                max_grade_point: $max_grade_point,
                completion_year: $completion_year,
                is_completed: $is_completed
            }]->(qt)
            
            CREATE (u)-[:STUDIED_AT]->(inst)
            CREATE (u)-[:STUDIED_FIELD]->(fs)
            """

            parameters = {
                "user_id": user.id,
                "qualification_id": qualification.id,
                "qual_type": qualification.qualification_type.value,
                "field_of_study": qualification.field_of_study,
                "institution_name": qualification.institution_name,
                "country": qualification.country,
                "degree_name": qualification.degree_name,
                "grade_point": qualification.grade_point,
                "max_grade_point": qualification.max_grade_point,
                "completion_year": qualification.completion_year,
                "is_completed": qualification.is_completed,
            }

            session.run(qual_query, parameters)

    def _create_interest_relationships(self, session: Session, user: User):
        """Create interest nodes and relationships"""
        for interest in user.interests:
            interest_query = """
            MERGE (fs:FieldOfStudy {name: $field_of_study})
            MERGE (u:User {user_id: $user_id})
            MERGE (u)-[:INTERESTED_IN {
                interest_id: $interest_id,
                interest_level: $interest_level
            }]->(fs)
            """

            parameters = {
                "user_id": user.id,
                "interest_id": interest.id,
                "field_of_study": interest.field_of_study,
                "interest_level": interest.interest_level,
            }

            session.run(interest_query, parameters)

    def _create_test_score_relationships(self, session: Session, user: User):
        """Create test score nodes and relationships"""
        for test_score in user.test_scores:
            test_query = """
            MERGE (tt:TestType {name: $test_type})
            MATCH (u:User {user_id: $user_id})
            CREATE (u)-[:HAS_TEST_SCORE {
                test_score_id: $test_score_id,
                score: $score,
                max_score: $max_score,
                test_date: $test_date,
                expiry_date: $expiry_date
            }]->(tt)
            """

            parameters = {
                "user_id": user.id,
                "test_score_id": test_score.id,
                "test_type": test_score.test_type,
                "score": test_score.score,
                "max_score": test_score.max_score,
                "test_date": (
                    test_score.test_date.isoformat() if test_score.test_date else None
                ),
                "expiry_date": (
                    test_score.expiry_date.isoformat()
                    if test_score.expiry_date
                    else None
                ),
            }

            session.run(test_query, parameters)

    def update_user_node(self, user: User) -> bool:
        """Update user node in Neo4j"""
        try:
            with self.db_manager.neo4j.get_db_session() as session:
                query = """
                MATCH (u:User {user_id: $user_id})
                SET u.email = $email,
                    u.first_name = $first_name,
                    u.last_name = $last_name,
                    u.date_of_birth = $date_of_birth,
                    u.nationality = $nationality,
                    u.phone = $phone,
                    u.updated_at = $updated_at
                RETURN u
                """

                parameters = {
                    "user_id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "date_of_birth": (
                        user.date_of_birth.isoformat() if user.date_of_birth else None
                    ),
                    "nationality": user.nationality,
                    "phone": user.phone,
                    "updated_at": (
                        user.updated_at.isoformat() if user.updated_at else None
                    ),
                }

                result = session.run(query, parameters)
                if result.single():
                    logger.info(
                        f"User node updated successfully in Neo4j: {user.email}"
                    )
                    return True
                else:
                    logger.warning(f"User node not found in Neo4j: {user.email}")
                    return False

        except Exception as e:
            logger.error(f"Failed to update user node in Neo4j: {e}")
            return False

    def delete_user_node(self, user_id: int) -> bool:
        """Delete user node and all relationships from Neo4j"""
        try:
            with self.db_manager.neo4j.get_db_session() as session:
                query = """
                MATCH (u:User {user_id: $user_id})
                DETACH DELETE u
                """

                result = session.run(query, {"user_id": user_id})
                logger.info(f"User node deleted successfully from Neo4j: {user_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to delete user node from Neo4j: {e}")
            return False

    def get_user_recommendations(
        self, user_id: int, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get program recommendations for a user based on their profile"""
        try:
            with self.db_manager.neo4j.get_db_session() as session:
                query = """
                MATCH (u:User {user_id: $user_id})
                
                // Get user's interests
                OPTIONAL MATCH (u)-[int_rel:INTERESTED_IN]->(fs:FieldOfStudy)
                
                // Get user's qualifications
                OPTIONAL MATCH (u)-[qual_rel:HAS_QUALIFICATION]->(qt:QualificationType)
                
                // Get user's test scores
                OPTIONAL MATCH (u)-[test_rel:HAS_TEST_SCORE]->(tt:TestType)
                
                // Find programs that match user's interests
                OPTIONAL MATCH (p:Program)-[:BELONGS_TO_FIELD]->(fs)
                WHERE p.is_active = true
                
                // Find programs that match user's qualification level
                OPTIONAL MATCH (p2:Program)-[:HAS_DEGREE_LEVEL]->(dl:DegreeLevel)
                WHERE p2.is_active = true AND (
                    (qt.type = 'bachelor' AND dl.level IN ['master', 'phd']) OR
                    (qt.type = 'master' AND dl.level = 'phd') OR
                    (qt.type = 'high_school' AND dl.level = 'bachelor')
                )
                
                // Get university information
                OPTIONAL MATCH (p)-[:OFFERED_BY]->(uni:University)
                OPTIONAL MATCH (p2)-[:OFFERED_BY]->(uni2:University)
                
                // Combine results and calculate match scores
                WITH u, 
                     COLLECT(DISTINCT {
                         program: p, 
                         university: uni, 
                         match_type: 'interest',
                         interest_level: int_rel.interest_level,
                         field: fs.name
                     }) as interest_matches,
                     COLLECT(DISTINCT {
                         program: p2, 
                         university: uni2, 
                         match_type: 'qualification',
                         qualification_type: qt.type,
                         degree_level: dl.level
                     }) as qualification_matches
                
                // Unwind and score matches
                WITH u, interest_matches + qualification_matches as all_matches
                UNWIND all_matches as match
                
                WITH u, match.program as program, match.university as university, 
                     match.match_type as match_type, match.interest_level as interest_level,
                     match.field as field, match.qualification_type as qual_type,
                     match.degree_level as degree_level
                
                WHERE program IS NOT NULL AND university IS NOT NULL
                
                // Calculate match score
                WITH program, university, match_type, interest_level, field, qual_type, degree_level,
                     CASE 
                         WHEN match_type = 'interest' AND interest_level = 'high' THEN 10
                         WHEN match_type = 'interest' AND interest_level = 'medium' THEN 7
                         WHEN match_type = 'interest' AND interest_level = 'low' THEN 5
                         WHEN match_type = 'qualification' THEN 8
                         ELSE 3
                     END as base_score,
                     
                     // Bonus for university ranking
                     CASE 
                         WHEN university.ranking_world <= 50 THEN 3
                         WHEN university.ranking_world <= 100 THEN 2
                         WHEN university.ranking_world <= 500 THEN 1
                         ELSE 0
                     END as ranking_bonus
                
                // Group by program and sum scores
                WITH program, university, 
                     SUM(base_score) + MAX(ranking_bonus) as total_score,
                     COLLECT(DISTINCT match_type) as match_types,
                     COLLECT(DISTINCT field) as matched_fields
                
                RETURN DISTINCT program.program_id as program_id,
                       program.name as program_name,
                       program.degree_level as degree_level,
                       program.field_of_study as field_of_study,
                       program.tuition_fee as tuition_fee,
                       program.currency as currency,
                       program.duration_years as duration_years,
                       program.language as language,
                       university.name as university_name,
                       university.city as university_city,
                       university.ranking_world as university_ranking,
                       total_score as match_score,
                       match_types,
                       matched_fields
                
                ORDER BY total_score DESC, university.ranking_world ASC
                LIMIT $limit
                """

                result = session.run(query, {"user_id": user_id, "limit": limit})
                recommendations = []

                for record in result:
                    recommendations.append(
                        {
                            "program_id": record["program_id"],
                            "program_name": record["program_name"],
                            "degree_level": record["degree_level"],
                            "field_of_study": record["field_of_study"],
                            "tuition_fee": record["tuition_fee"],
                            "currency": record["currency"],
                            "duration_years": record["duration_years"],
                            "language": record["language"],
                            "university_name": record["university_name"],
                            "university_city": record["university_city"],
                            "university_ranking": record["university_ranking"],
                            "match_score": record["match_score"],
                            "match_types": record["match_types"],
                            "matched_fields": record["matched_fields"],
                        }
                    )

                return recommendations

        except Exception as e:
            logger.error(f"Failed to get user recommendations from Neo4j: {e}")
            return []

    def create_program_nodes(self, programs: List[Any]) -> bool:
        """Create program nodes in Neo4j for recommendation purposes"""
        try:
            with self.db_manager.neo4j.get_db_session() as session:
                for program in programs:
                    query = """
                    MERGE (p:Program {
                        program_id: $program_id,
                        name: $name,
                        degree_level: $degree_level,
                        field_of_study: $field_of_study,
                        duration_years: $duration_years,
                        language: $language,
                        tuition_fee: $tuition_fee,
                        currency: $currency
                    })
                    
                    MERGE (fs:FieldOfStudy {name: $field_of_study})
                    MERGE (dl:DegreeLevel {level: $degree_level})
                    MERGE (uni:University {
                        university_id: $university_id,
                        name: $university_name
                    })
                    
                    CREATE (p)-[:FIELD_OF_STUDY]->(fs)
                    CREATE (p)-[:DEGREE_LEVEL]->(dl)
                    CREATE (p)-[:OFFERED_BY]->(uni)
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
                        "university_id": program.university_id,
                        "university_name": (
                            program.university.name if program.university else None
                        ),
                    }

                    session.run(query, parameters)

                logger.info(f"Created {len(programs)} program nodes in Neo4j")
                return True

        except Exception as e:
            logger.error(f"Failed to create program nodes in Neo4j: {e}")
            return False

    def create_interest_relationship(
        self, user_id: int, interest: UserInterest
    ) -> bool:
        """Create a single interest relationship in Neo4j"""
        try:
            with self.db_manager.neo4j.get_db_session() as session:
                interest_query = """
                MERGE (fs:FieldOfStudy {name: $field_of_study})
                MERGE (u:User {user_id: $user_id})
                MERGE (u)-[:INTERESTED_IN {
                    interest_id: $interest_id,
                    interest_level: $interest_level
                }]->(fs)
                """

                parameters = {
                    "user_id": user_id,
                    "interest_id": interest.id,
                    "field_of_study": interest.field_of_study,
                    "interest_level": interest.interest_level,
                }

                session.run(interest_query, parameters)
                logger.info(
                    f"Interest relationship created in Neo4j for user {user_id}"
                )
                return True

        except Exception as e:
            logger.error(f"Failed to create interest relationship in Neo4j: {e}")
            return False

    def delete_interest_relationship(self, interest_id: int) -> bool:
        """Delete a specific interest relationship from Neo4j"""
        try:
            with self.db_manager.neo4j.get_db_session() as session:
                query = """
                MATCH (u:User)-[r:INTERESTED_IN]->(fs:FieldOfStudy)
                WHERE r.interest_id = $interest_id
                DELETE r
                """

                session.run(query, {"interest_id": interest_id})
                logger.info(f"Interest relationship deleted from Neo4j: {interest_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to delete interest relationship from Neo4j: {e}")
            return False

    def update_interest_relationship(
        self, user_id: int, interest: UserInterest
    ) -> bool:
        """Update a specific interest relationship in Neo4j"""
        try:
            with self.db_manager.neo4j.get_db_session() as session:
                query = """
                MATCH (u:User {user_id: $user_id})-[r:INTERESTED_IN]->(fs:FieldOfStudy)
                WHERE r.interest_id = $interest_id
                SET r.interest_level = $interest_level
                
                WITH u, r
                MATCH (new_fs:FieldOfStudy {name: $field_of_study})
                DELETE r
                
                WITH u, new_fs
                MERGE (u)-[:INTERESTED_IN {
                    interest_id: $interest_id,
                    interest_level: $interest_level
                }]->(new_fs)
                """

                parameters = {
                    "user_id": user_id,
                    "interest_id": interest.id,
                    "field_of_study": interest.field_of_study,
                    "interest_level": interest.interest_level,
                }

                session.run(query, parameters)
                logger.info(
                    f"Interest relationship updated in Neo4j for user {user_id}"
                )
                return True

        except Exception as e:
            logger.error(f"Failed to update interest relationship in Neo4j: {e}")
            return False

    def get_user_interests_from_neo4j(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user interests from Neo4j"""
        try:
            with self.db_manager.neo4j.get_db_session() as session:
                query = """
                MATCH (u:User {user_id: $user_id})-[r:INTERESTED_IN]->(fs:FieldOfStudy)
                RETURN r.interest_id as interest_id,
                       fs.name as field_of_study,
                       r.interest_level as interest_level
                ORDER BY r.interest_level DESC, fs.name ASC
                """

                result = session.run(query, {"user_id": user_id})
                interests = []

                for record in result:
                    interests.append(
                        {
                            "interest_id": record["interest_id"],
                            "field_of_study": record["field_of_study"],
                            "interest_level": record["interest_level"],
                        }
                    )

                return interests

        except Exception as e:
            logger.error(f"Failed to get user interests from Neo4j: {e}")
            return []

    def create_qualification_status_relationship(
        self, user_id: int, program_id: int, qualification_data: Dict[str, Any]
    ) -> bool:
        """Create or update qualification status relationship in Neo4j"""
        try:
            with self.db_manager.neo4j.get_db_session() as session:
                # First, ensure program node exists
                program_query = """
                MERGE (p:Program {program_id: $program_id})
                """
                session.run(program_query, {"program_id": program_id})

                # Create or update qualification status relationship
                query = """
                MATCH (u:User {user_id: $user_id})
                MATCH (p:Program {program_id: $program_id})
                MERGE (u)-[r:HAS_QUALIFICATION]->(p)
                SET r.is_qualified = $is_qualified,
                    r.qualification_score = $qualification_score,
                    r.requirements_met = $requirements_met,
                    r.total_requirements = $total_requirements,
                    r.missing_requirements = $missing_requirements,
                    r.checked_at = $checked_at,
                    r.updated_at = $updated_at
                RETURN r
                """

                parameters = {
                    "user_id": user_id,
                    "program_id": program_id,
                    "is_qualified": qualification_data.get("is_qualified", False),
                    "qualification_score": qualification_data.get(
                        "qualification_score", 0.0
                    ),
                    "requirements_met": qualification_data.get("requirements_met", 0),
                    "total_requirements": qualification_data.get(
                        "total_requirements", 0
                    ),
                    "missing_requirements": str(
                        qualification_data.get("missing_requirements", [])
                    ),
                    "checked_at": qualification_data.get(
                        "checked_at", datetime.utcnow()
                    ).isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                }

                session.run(query, parameters)
                logger.info(
                    f"Qualification status relationship created/updated in Neo4j for user {user_id}, program {program_id}"
                )
                return True

        except Exception as e:
            logger.error(
                f"Failed to create qualification status relationship in Neo4j: {e}"
            )
            return False

    def get_user_qualification_status_from_neo4j(
        self, user_id: int, program_id: int = None
    ) -> List[Dict[str, Any]]:
        """Get user qualification status from Neo4j"""
        try:
            with self.db_manager.neo4j.get_db_session() as session:
                if program_id:
                    # Get specific program qualification status
                    query = """
                    MATCH (u:User {user_id: $user_id})-[r:QUALIFIED_FOR]->(p:Program {program_id: $program_id})
                    RETURN p.program_id as program_id,
                           r.is_qualified as is_qualified,
                           r.qualification_score as qualification_score,
                           r.requirements_met as requirements_met,
                           r.total_requirements as total_requirements,
                           r.missing_requirements as missing_requirements,
                           r.checked_at as checked_at
                    """
                    result = session.run(
                        query, {"user_id": user_id, "program_id": program_id}
                    )
                else:
                    # Get all qualification statuses for user
                    query = """
                    MATCH (u:User {user_id: $user_id})-[r:QUALIFIED_FOR]->(p:Program)
                    RETURN p.program_id as program_id,
                           r.is_qualified as is_qualified,
                           r.qualification_score as qualification_score,
                           r.requirements_met as requirements_met,
                           r.total_requirements as total_requirements,
                           r.missing_requirements as missing_requirements,
                           r.checked_at as checked_at
                    ORDER BY r.qualification_score DESC
                    """
                    result = session.run(query, {"user_id": user_id})

                statuses = []
                for record in result:
                    statuses.append(
                        {
                            "program_id": record["program_id"],
                            "is_qualified": record["is_qualified"],
                            "qualification_score": record["qualification_score"],
                            "requirements_met": record["requirements_met"],
                            "total_requirements": record["total_requirements"],
                            "missing_requirements": record["missing_requirements"],
                            "checked_at": record["checked_at"],
                        }
                    )

                return statuses

        except Exception as e:
            logger.error(f"Failed to get user qualification status from Neo4j: {e}")
            return []

    def get_qualified_programs_recommendations(
        self, user_id: int, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get program recommendations based on qualification status from Neo4j"""
        try:
            with self.db_manager.neo4j.get_db_session() as session:
                query = """
                MATCH (u:User {user_id: $user_id})-[r:QUALIFIED_FOR]->(p:Program)
                WHERE r.is_qualified = true OR r.qualification_score >= 80
                RETURN p.program_id as program_id,
                       r.qualification_score as qualification_score,
                       r.is_qualified as is_qualified,
                       r.checked_at as checked_at
                ORDER BY r.qualification_score DESC, r.checked_at DESC
                LIMIT $limit
                """

                result = session.run(query, {"user_id": user_id, "limit": limit})
                recommendations = []

                for record in result:
                    recommendations.append(
                        {
                            "program_id": record["program_id"],
                            "qualification_score": record["qualification_score"],
                            "is_qualified": record["is_qualified"],
                            "checked_at": record["checked_at"],
                            "recommendation_reason": "High qualification match",
                        }
                    )

                return recommendations

        except Exception as e:
            logger.error(
                f"Failed to get qualified programs recommendations from Neo4j: {e}"
            )
            return []
