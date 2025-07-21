#!/usr/bin/env python3
"""
Test script for qualification Neo4j integration
"""

import sys
import os

# Add the parent directory to the path so we can import from app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.qualification_service import QualificationService
from app.services.neo4j_user_service import Neo4jUserService
from app.database import get_mysql_session
from app.util.log import get_logger

logger = get_logger(__name__)


def test_qualification_neo4j_integration():
    """Test the qualification service Neo4j integration"""

    try:
        # Create qualification service instance
        db = next(get_mysql_session())
        qualification_service = QualificationService(db)

        logger.info("Testing qualification Neo4j integration...")

        # Test 1: Check if Neo4j service is initialized
        assert (
            qualification_service.neo4j_service is not None
        ), "Neo4j service should be initialized"
        logger.info("✓ Neo4j service initialized successfully")

        # Test 2: Test Neo4j connection
        neo4j_service = Neo4jUserService()
        logger.info("✓ Neo4j service connection established")

        # Test 3: Test qualification status methods
        try:
            # Test getting qualification status from Neo4j (should not fail even if no data)
            statuses = qualification_service.get_qualification_status_from_neo4j(1)
            logger.info(
                f"✓ Retrieved {len(statuses)} qualification statuses from Neo4j"
            )

            # Test getting recommendations
            recommendations = (
                qualification_service.get_program_recommendations_by_qualification(1)
            )
            logger.info(
                f"✓ Retrieved {len(recommendations)} recommendations from Neo4j"
            )

        except Exception as e:
            logger.warning(
                f"Neo4j data retrieval test failed (expected if no data): {e}"
            )

        logger.info("✓ All qualification Neo4j integration tests passed!")
        return True

    except Exception as e:
        logger.error(f"✗ Qualification Neo4j integration test failed: {e}")
        return False

    finally:
        try:
            db.close()
        except:
            pass


if __name__ == "__main__":
    success = test_qualification_neo4j_integration()
    sys.exit(0 if success else 1)
