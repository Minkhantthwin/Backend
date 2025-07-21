from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.routes import (
    user,
    health,
    user_qualification,
    user_interest,
    user_test_score,
    program,
    application,
    qualification,
    region,
    university,
    recommendation,
)
import logging
from app.util.log import get_logger
from app.util.env_config import Settings
from app.database import get_database_manager

logging.basicConfig(level=logging.INFO)
logger = get_logger(__name__)
settings = Settings()

# Initialize database connections
db_manager = get_database_manager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    try:
        db_manager.initialize_all()
        # Create tables if they don't exist
        db_manager.mysql.create_tables()
        logger.info("Application and databases initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise

    yield

    # Shutdown
    try:
        db_manager.close_all()
        logger.info("Application shutdown completed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    lifespan=lifespan,
)

# Include routers
app.include_router(user.router, prefix=f"/api/{settings.API_V1_STR}", tags=["Users"])

app.include_router(
    user_interest.router, prefix=f"/api/{settings.API_V1_STR}", tags=["User Interests"]
)
app.include_router(
    user_test_score.router,
    prefix=f"/api/{settings.API_V1_STR}",
    tags=["User Test Scores"],
)
app.include_router(
    program.router, prefix=f"/api/{settings.API_V1_STR}", tags=["Programs"]
)
app.include_router(
    application.router, prefix=f"/api/{settings.API_V1_STR}", tags=["Applications"]
)
app.include_router(
    qualification.router, prefix=f"/api/{settings.API_V1_STR}", tags=["Qualifications"]
)
app.include_router(
    region.router, prefix=f"/api/{settings.API_V1_STR}", tags=["Regions"]
)
app.include_router(
    university.router, prefix=f"/api/{settings.API_V1_STR}", tags=["Universities"]
)
app.include_router(
    recommendation.router,
    prefix=f"/api/{settings.API_V1_STR}",
    tags=["Recommendations"],
)
app.include_router(health.router, tags=["Health"])


def main():
    logger.info("Application started")
    try:
        logger.debug("This is a debug message")
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
    finally:
        logger.info("Application ended")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.HOST, port=settings.PORT, reload=settings.RELOAD)
