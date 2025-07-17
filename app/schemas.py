from pydantic import BaseModel, EmailStr, field_validator, Field
from typing import Optional, List
from datetime import datetime, date
import re
from enum import Enum


class QualificationTypeEnum(str, Enum):
    HIGH_SCHOOL = "high_school"
    BACHELOR = "bachelor"
    MASTER = "master"
    PHD = "phd"
    DIPLOMA = "diploma"
    CERTIFICATE = "certificate"


class InterestLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class UserQualificationCreate(BaseModel):
    """Schema for creating user qualifications"""

    qualification_type: QualificationTypeEnum
    institution_name: Optional[str] = None
    degree_name: Optional[str] = None
    field_of_study: Optional[str] = None
    grade_point: Optional[str] = None
    max_grade_point: Optional[str] = None
    completion_year: Optional[int] = None
    country: Optional[str] = None
    is_completed: bool = False


class QualificationCheckResponse(BaseModel):
    """Schema for qualification check response"""

    user_id: int
    program_id: int
    program_name: str
    university_name: str
    is_qualified: bool
    qualification_score: float
    requirements_met: int
    total_requirements: int
    missing_requirements: List[dict]
    detailed_results: List[dict]
    checked_at: datetime


class QualificationSummaryResponse(BaseModel):
    """Schema for qualification summary response"""

    user_id: int
    qualified_programs: List[dict]
    partially_qualified: List[dict]
    not_qualified: List[dict]
    total_programs_checked: int


class UserInterestCreate(BaseModel):
    """Schema for creating user interests"""

    field_of_study: str
    interest_level: str = "medium"


class UserTestScoreCreate(BaseModel):
    """Schema for creating user test scores"""

    test_type: str
    score: str
    max_score: Optional[str] = None
    test_date: Optional[date] = None
    expiry_date: Optional[date] = None


class UserBase(BaseModel):
    """Base user schema with common fields"""

    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[date] = None
    nationality: Optional[str] = Field(None, max_length=100)

    @field_validator("phone")
    @classmethod
    def validate_phone_number(cls, v):
        """Validate phone number format"""
        if v is not None:
            # Remove all non-digit characters for validation
            digits_only = re.sub(r"\D", "", v)
            if len(digits_only) < 10 or len(digits_only) > 15:
                raise ValueError("Phone number must be between 10 and 15 digits")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, v):
        """Validate date of birth is not in the future"""
        if v is not None and v > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return v


class UserCreate(UserBase):
    """Schema for creating a new user"""

    password: str = Field(..., min_length=8, max_length=100)
    qualifications: Optional[List[UserQualificationCreate]] = []
    interests: Optional[List[UserInterestCreate]] = []
    test_scores: Optional[List[UserTestScoreCreate]] = []

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("Password must contain at least one letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        return v


class UserUpdate(BaseModel):
    """Schema for updating user information"""

    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[date] = None
    nationality: Optional[str] = Field(None, max_length=100)

    @field_validator("phone")
    @classmethod
    def validate_phone_number(cls, v):
        """Validate phone number format"""
        if v is not None:
            digits_only = re.sub(r"\D", "", v)
            if len(digits_only) < 10 or len(digits_only) > 15:
                raise ValueError("Phone number must be between 10 and 15 digits")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, v):
        """Validate date of birth is not in the future"""
        if v is not None and v > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return v


class UserQualificationResponse(BaseModel):
    """Schema for user qualification response"""

    id: int
    qualification_type: str
    institution_name: Optional[str]
    degree_name: Optional[str]
    field_of_study: Optional[str]
    grade_point: Optional[str]
    max_grade_point: Optional[str]
    completion_year: Optional[int]
    country: Optional[str]
    is_completed: bool

    class Config:
        from_attributes = True


class UserInterestResponse(BaseModel):
    """Schema for user interest response"""

    id: int
    field_of_study: str
    interest_level: str

    class Config:
        from_attributes = True


class UserTestScoreResponse(BaseModel):
    """Schema for user test score response"""

    id: int
    test_type: str
    score: str
    max_score: Optional[str]
    test_date: Optional[date]
    expiry_date: Optional[date]

    class Config:
        from_attributes = True


class UserResponse(UserBase):
    """Schema for user response"""

    id: int
    created_at: datetime
    updated_at: datetime
    qualifications: Optional[List[UserQualificationResponse]] = []
    interests: Optional[List[UserInterestResponse]] = []
    test_scores: Optional[List[UserTestScoreResponse]] = []

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Schema for paginated user list response"""

    users: list[UserResponse]
    total: int
    page: int
    per_page: int
    pages: int


class MessageResponse(BaseModel):
    """Schema for simple message responses"""

    message: str


# University and Program related schemas


class DegreeLevel(str, Enum):
    BACHELOR = "bachelor"
    MASTER = "master"
    PHD = "phd"
    DIPLOMA = "diploma"
    CERTIFICATE = "certificate"


class ApplicationStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WAITLISTED = "waitlisted"


class RegionBase(BaseModel):
    """Base schema for region"""

    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=2, max_length=3)


class RegionCreate(RegionBase):
    """Schema for creating a country"""

    pass


class RegionResponse(RegionBase):
    """Schema for country response"""

    id: int

    class Config:
        from_attributes = True


class UniversityBase(BaseModel):
    """Base schema for university"""

    name: str = Field(..., min_length=1, max_length=255)
    region_id: int
    city: Optional[str] = Field(None, max_length=100)
    established_year: Optional[int] = None
    type: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    ranking_world: Optional[int] = None
    ranking_national: Optional[int] = None


class UniversityCreate(UniversityBase):
    """Schema for creating a university"""

    pass


class UniversityResponse(UniversityBase):
    """Schema for university response"""

    id: int
    created_at: datetime
    country: Optional[RegionResponse] = None

    class Config:
        from_attributes = True


class ProgramRequirementBase(BaseModel):
    """Base schema for program requirements"""

    requirement_type: str = Field(..., max_length=50)
    requirement_value: str = Field(..., max_length=255)
    test_type: Optional[str] = Field(None, max_length=50)
    is_mandatory: bool = True
    description: Optional[str] = None


class ProgramRequirementCreate(ProgramRequirementBase):
    """Schema for creating program requirements"""

    pass


class ProgramRequirementResponse(ProgramRequirementBase):
    """Schema for program requirement response"""

    id: int
    program_id: int

    class Config:
        from_attributes = True


class ProgramBase(BaseModel):
    """Base schema for program"""

    university_id: int
    name: str = Field(..., min_length=1, max_length=255)
    degree_level: DegreeLevel
    field_of_study: str = Field(..., max_length=255)
    duration_years: Optional[float] = None
    language: str = Field(default="English", max_length=50)
    tuition_fee: Optional[float] = None
    currency: str = Field(default="USD", max_length=3)
    application_deadline: Optional[date] = None
    start_date: Optional[date] = None
    description: Optional[str] = None
    is_active: bool = True


class ProgramCreate(ProgramBase):
    """Schema for creating a program"""

    requirements: List[ProgramRequirementCreate] = Field(
        default_factory=list,
    )


class ProgramResponse(ProgramBase):
    """Schema for program response"""

    id: int
    university: Optional[UniversityResponse] = None
    requirements: Optional[List[ProgramRequirementResponse]] = []

    class Config:
        from_attributes = True


class ApplicationBase(BaseModel):
    """Base schema for application"""

    user_id: int
    program_id: int
    personal_statement: Optional[str] = None
    additional_documents: Optional[dict] = None


class ApplicationCreate(ApplicationBase):
    """Schema for creating an application"""

    pass


class ApplicationUpdate(BaseModel):
    """Schema for updating an application"""

    status: Optional[ApplicationStatus] = None
    personal_statement: Optional[str] = None
    additional_documents: Optional[dict] = None
    decision_date: Optional[datetime] = None


class ApplicationResponse(ApplicationBase):
    """Schema for application response"""

    id: int
    status: ApplicationStatus
    application_date: datetime
    decision_date: Optional[datetime] = None
    user: Optional[UserResponse] = None
    program: Optional[ProgramResponse] = None

    class Config:
        from_attributes = True


class RecommendationRequest(BaseModel):
    """Schema for recommendation request"""

    user_id: int
    preferred_countries: Optional[List[str]] = []
    preferred_fields: Optional[List[str]] = []
    degree_level: Optional[DegreeLevel] = None
    max_tuition_fee: Optional[float] = None
    language_preference: Optional[str] = None


class RecommendationResponse(BaseModel):
    """Schema for recommendation response"""

    program: ProgramResponse
    match_score: float
    matching_factors: List[str]
    recommendation_reasons: List[str]


class RecommendationListResponse(BaseModel):
    """Schema for recommendation list response"""
    
    user_id: int
    recommendations: List[dict]
    total_recommendations: int


class UserRecommendationResponse(BaseModel):
    """Schema for user recommendation response"""
    
    program_id: int
    program_name: str
    degree_level: str
    match_score: int

    recommendations: List[RecommendationResponse]
    total: int
    user_id: int
    request_parameters: RecommendationRequest
