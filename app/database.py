from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable
from neomodel import config, db
import logging
from typing import Optional
from contextlib import contextmanager

from app.util.env_config import Settings

logger = logging.getLogger(__name__)

# SQLAlchemy Base
Base = declarative_base()


class MySQLDatabase:
    """MySQL database connection and session management"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._engine = None
        self._session_local = None

    def initialize(self):
        """Initialize MySQL database connection"""
        try:
            # Create MySQL connection URL
            database_url = (
                f"mysql+pymysql://{self.settings.MYSQL_USER}:"
                f"{self.settings.MYSQL_PASSWORD}@"
                f"{self.settings.MYSQL_HOST}:{self.settings.MYSQL_PORT}/"
                f"{self.settings.MYSQL_DATABASE}?"
                f"charset={self.settings.MYSQL_CHARSET}"
            )

            # Create engine with connection pool
            self._engine = create_engine(
                database_url,
                poolclass=QueuePool,
                pool_size=self.settings.MYSQL_POOL_SIZE,
                max_overflow=self.settings.MYSQL_MAX_OVERFLOW,
                pool_timeout=self.settings.MYSQL_POOL_TIMEOUT,
                pool_recycle=self.settings.MYSQL_POOL_RECYCLE,
                echo=self.settings.DEBUG,
                echo_pool=self.settings.DEBUG,
            )

            # Create session factory
            self._session_local = sessionmaker(
                autocommit=False, autoflush=False, bind=self._engine
            )

            logger.info("MySQL database connection initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize MySQL database: {e}")
            raise

    @property
    def engine(self):
        """Get SQLAlchemy engine"""
        if self._engine is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._engine

    @property
    def session_local(self):
        """Get session factory"""
        if self._session_local is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._session_local

    def get_session(self):
        """Get database session"""
        session = self.session_local()
        try:
            return session
        except Exception:
            session.close()
            raise

    @contextmanager
    def get_db_session(self):
        """Context manager for database sessions"""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def create_tables(self):
        """Create all tables defined in models"""
        try:
            from app.models import Base

            Base.metadata.create_all(bind=self.engine)
            # Ensure new columns exist (lightweight migration)
            try:
                from sqlalchemy import text

                with self.engine.connect() as conn:
                    # Check if supporting_documents column exists
                    check_sql = text(
                        """
                        SELECT COUNT(*) AS cnt FROM information_schema.COLUMNS
                        WHERE TABLE_SCHEMA = DATABASE()
                          AND TABLE_NAME = 'applications'
                          AND COLUMN_NAME = 'supporting_documents'
                        """
                    )
                    result = conn.execute(check_sql).fetchone()
                    exists = bool(result[0]) if result is not None else False
                    if not exists:
                        # Add the column
                        try:
                            conn.execute(
                                text(
                                    "ALTER TABLE applications ADD COLUMN supporting_documents JSON NULL"
                                )
                            )
                            logger.info(
                                "Added missing column 'supporting_documents' to applications table"
                            )
                        except Exception as e:
                            logger.error(
                                f"Failed to add 'supporting_documents' column: {e}"
                            )
            except Exception as e:
                logger.warning(f"Column verification step failed: {e}")
            logger.info("MySQL tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create MySQL tables: {e}")
            raise

    def test_connection(self) -> bool:
        """Test MySQL database connection"""
        try:
            from sqlalchemy import text

            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            logger.info("MySQL connection test successful")
            return True
        except Exception as e:
            logger.error(f"MySQL connection test failed: {e}")
            return False

    def close(self):
        """Close database connections"""
        if self._engine:
            self._engine.dispose()
            logger.info("MySQL database connections closed")


class Neo4jDatabase:
    """Neo4j database connection and session management"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._driver = None

    def initialize(self):
        """Initialize Neo4j database connection"""
        try:
            # Initialize neomodel configuration
            config.DATABASE_URL = (
                f"bolt://{self.settings.NEO4J_USER}:"
                f"{self.settings.NEO4J_PASSWORD}@"
                f"{self.settings.NEO4J_URI.replace('bolt://', '')}"
            )

            # Create Neo4j driver
            self._driver = GraphDatabase.driver(
                self.settings.NEO4J_URI,
                auth=(self.settings.NEO4J_USER, self.settings.NEO4J_PASSWORD),
                max_connection_lifetime=self.settings.NEO4J_MAX_CONNECTION_LIFETIME,
                max_connection_pool_size=self.settings.NEO4J_MAX_CONNECTION_POOL_SIZE,
                connection_acquisition_timeout=self.settings.NEO4J_CONNECTION_ACQUISITION_TIMEOUT,
            )

            # Test the connection
            self._driver.verify_connectivity()

            logger.info("Neo4j database connection initialized successfully")

        except ServiceUnavailable as e:
            logger.error(f"Neo4j service unavailable: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j database: {e}")
            raise

    @property
    def driver(self):
        """Get Neo4j driver"""
        if self._driver is None:
            raise RuntimeError(
                "Neo4j database not initialized. Call initialize() first."
            )
        return self._driver

    def get_session(self, database: Optional[str] = None):
        """Get Neo4j session"""
        database = database or self.settings.NEO4J_DATABASE
        return self.driver.session(database=database)

    @contextmanager
    def get_db_session(self, database: Optional[str] = None):
        """Context manager for Neo4j sessions"""
        session = self.get_session(database)
        try:
            yield session
        finally:
            session.close()

    def execute_query(
        self, query: str, parameters: dict = None, database: Optional[str] = None
    ):
        """Execute a Cypher query"""
        with self.get_db_session(database) as session:
            result = session.run(query, parameters or {})
            return [record for record in result]

    def execute_write_transaction(
        self, transaction_function, *args, database: Optional[str] = None, **kwargs
    ):
        """Execute a write transaction"""
        with self.get_db_session(database) as session:
            return session.execute_write(transaction_function, *args, **kwargs)

    def execute_read_transaction(
        self, transaction_function, *args, database: Optional[str] = None, **kwargs
    ):
        """Execute a read transaction"""
        with self.get_db_session(database) as session:
            return session.execute_read(transaction_function, *args, **kwargs)

    def test_connection(self) -> bool:
        """Test Neo4j database connection"""
        try:
            with self.get_db_session() as session:
                result = session.run("RETURN 1 AS test")
                record = result.single()
                if record and record["test"] == 1:
                    logger.info("Neo4j connection test successful")
                    return True
                return False
        except Exception as e:
            logger.error(f"Neo4j connection test failed: {e}")
            return False

    def close(self):
        """Close Neo4j driver"""
        if self._driver:
            self._driver.close()
            logger.info("Neo4j database connections closed")


class DatabaseManager:
    """Central database manager for both MySQL and Neo4j"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.mysql = MySQLDatabase(settings)
        self.neo4j = Neo4jDatabase(settings)

    def initialize_all(self):
        """Initialize both databases"""
        logger.info("Initializing databases...")

        # Initialize MySQL
        self.mysql.initialize()

        # Initialize Neo4j
        self.neo4j.initialize()

        logger.info("All databases initialized successfully")

    def test_all_connections(self) -> dict:
        """Test all database connections"""
        results = {
            "mysql": self.mysql.test_connection(),
            "neo4j": self.neo4j.test_connection(),
        }

        if all(results.values()):
            logger.info("All database connections are healthy")
        else:
            logger.warning(f"Database connection status: {results}")

        return results

    def close_all(self):
        """Close all database connections"""
        self.mysql.close()
        self.neo4j.close()
        logger.info("All database connections closed")


# Global database manager instance
db_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance"""
    global db_manager
    if db_manager is None:
        settings = Settings()
        db_manager = DatabaseManager(settings)
    return db_manager


def get_mysql_session():
    """Dependency to get MySQL database session"""
    db_mgr = get_database_manager()
    session = db_mgr.mysql.get_session()
    try:
        yield session
    finally:
        session.close()


def get_neo4j_session():
    """Dependency to get Neo4j database session"""
    db_mgr = get_database_manager()
    with db_mgr.neo4j.get_db_session() as session:
        yield session
