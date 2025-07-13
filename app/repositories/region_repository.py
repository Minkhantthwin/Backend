from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from app.models import Region
from app.schemas import RegionCreate
import logging

logger = logging.getLogger(__name__)


class RegionRepository:

    def __init__(self, db: Session):
        self.db = db

    def create_region(self, region_data: RegionCreate) -> Region:
        try:
            db_region = Region(**region_data.model_dump())
            self.db.add(db_region)
            self.db.commit()
            self.db.refresh(db_region)
            logger.info(f"Region created successfully: {db_region.name}")
            return db_region
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Failed to create region due to integrity constraint: {e}")
            raise ValueError("Region name or code already exists")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create region: {e}")
            raise

    def get_region_by_id(self, region_id: int) -> List[Region]:
        try:
            region = self.db.query(Region).filter(Region.id == region_id).first()
            return region
        except Exception as e:
            logger.error(f"Failed to get region by ID {region_id}: {e}")
            raise

    def get_regions(self, skip: int = 0, limit: int = 100) -> List[Region]:
        try:
            regions = self.db.query(Region).offset(skip).limit(limit).all()
            return regions
        except Exception as e:
            logger.error(f"Failed to get regions: {e}")
            raise

    def update_region(
        self, region_id: int, region_data: RegionCreate
    ) -> Optional[Region]:
        try:
            region = self.get_region_by_id(region_id)
            if not region:
                return None
            for field, value in region_data.model_dump().items():
                setattr(region, field, value)
            self.db.commit()
            self.db.refresh(region)
            logger.info(f"Region updated successfully: {region.name}")
            return region
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Failed to update region due to integrity constraint: {e}")
            raise ValueError("Region name or code already exists")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update region: {e}")
            raise

    def delete_region(self, region_id: int) -> bool:
        try:
            region = self.get_region_by_id(region_id)
            if not region:
                return False
            self.db.delete(region)
            self.db.commit()
            logger.info(f"Region deleted successfully: {region.name}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete region: {e}")
            raise
