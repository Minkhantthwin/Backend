from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Text,
    Date,
    JSON,
    Enum,
    ForeignKey,
)
from sqlalchemy.types import Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class QualificationType(enum.Enum):
    HIGH_SCHOOL = "high_school"
    BACHELOR = "bachelor"
    MASTER = "master"
    PHD = "phd"
    DIPLOMA = "diploma"
    CERTIFICATE = "certificate"


class DegreeLevel(enum.Enum):
    BACHELOR = "bachelor"
    MASTER = "master"
    PHD = "phd"
    DIPLOMA = "diploma"
    CERTIFICATE = "certificate"


class ApplicationStatus(enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WAITLISTED = "waitlisted"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    password_hash = Column(String(255))
    first_name = Column(String(100))
    last_name = Column(String(100))
    date_of_birth = Column(Date)
    nationality = Column(String(100))
    phone = Column(String(20))
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    qualifications = relationship("UserQualification", back_populates="user")
    interests = relationship("UserInterest", back_populates="user")
    applications = relationship("Application", back_populates="user")
    test_scores = relationship("UserTestScore", back_populates="user")


class University(Base):
    __tablename__ = "universities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    region_id = Column(Integer, ForeignKey("regions.id"))
    city = Column(String(100))
    established_year = Column(Integer)
    type = Column(String(20))
    website = Column(String(255))
    description = Column(Text)
    ranking_world = Column(Integer)
    ranking_national = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    programs = relationship("Program", back_populates="university")
    region = relationship("Region", back_populates="universities")


class Program(Base):
    __tablename__ = "programs"

    id = Column(Integer, primary_key=True, index=True)
    university_id = Column(Integer, ForeignKey("universities.id"))
    name = Column(String(255))
    degree_level = Column(Enum(DegreeLevel))
    field_of_study = Column(String(255))
    duration_years = Column(Numeric(2, 1))
    language = Column(String(50), default="English")
    tuition_fee = Column(Numeric(10, 2))
    currency = Column(String(3), default="USD")
    application_deadline = Column(Date)
    start_date = Column(Date)
    description = Column(Text)
    is_active = Column(Boolean, default=True)

    university = relationship("University", back_populates="programs")
    requirements = relationship("ProgramRequirement", back_populates="program")
    applications = relationship("Application", back_populates="program")


class UserQualification(Base):
    __tablename__ = "user_qualifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    qualification_type = Column(Enum(QualificationType))
    institution_name = Column(String(255))
    degree_name = Column(String(255))
    field_of_study = Column(String(255))
    grade_point = Column(String(10))
    max_grade_point = Column(String(10))
    completion_year = Column(Integer)
    country = Column(String(100))
    is_completed = Column(Boolean, default=False)

    user = relationship("User", back_populates="qualifications")


class UserQualificationStatus(Base):
    __tablename__ = "user_qualification_status"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    program_id = Column(Integer, ForeignKey("programs.id"))
    is_qualified = Column(Boolean, default=False)
    qualification_score = Column(Numeric(5, 2))
    missing_requirements = Column(JSON)
    last_checked = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    program = relationship("Program")


class UserInterest(Base):
    __tablename__ = "user_interests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    field_of_study = Column(String(255))
    interest_level = Column(String(20), default="medium")

    user = relationship("User", back_populates="interests")


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    program_id = Column(Integer, ForeignKey("programs.id"))
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.DRAFT)
    application_date = Column(DateTime, default=datetime.utcnow)
    decision_date = Column(DateTime)
    personal_statement = Column(Text)
    additional_documents = Column(JSON)
    # Stores metadata about files saved on disk under the documents/ folder
    # Example: [{"id": str, "filename": str, "content_type": str, "size": int, "path": str, "uploaded_at": str}]
    supporting_documents = Column(JSON)

    user = relationship("User", back_populates="applications")
    program = relationship("Program", back_populates="applications")


class Region(Base):
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True)
    code = Column(String(3), unique=True)

    universities = relationship("University", back_populates="region")


class ProgramRequirement(Base):
    __tablename__ = "program_requirements"

    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey("programs.id"))
    requirement_type = Column(String(50))
    requirement_value = Column(String(255))
    test_type = Column(String(50))
    is_mandatory = Column(Boolean, default=True)
    description = Column(Text)

    program = relationship("Program", back_populates="requirements")


class UserTestScore(Base):
    __tablename__ = "user_test_scores"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    test_type = Column(String(20))
    score = Column(String(20))
    max_score = Column(String(20))
    test_date = Column(Date)
    expiry_date = Column(Date)

    user = relationship("User", back_populates="test_scores")
