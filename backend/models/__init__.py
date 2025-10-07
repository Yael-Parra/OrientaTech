# Modelos de autenticación
from .auth import UserRegister, UserLogin, UserResponse, Token, TokenData

# Modelos de documentos
from .documents import (
    DocumentType, DocumentUploadResponse, DocumentInfo, 
    UserDocumentsResponse, DocumentDeleteResponse, 
    DocumentValidationError, DocumentUploadRequest,
    UserFolderInfo, DocumentValidator, DocumentErrorResponses
)

# Modelos de perfil de usuario
from .user_profile import (
    GenderEnum, EducationLevelEnum, DigitalLevelEnum,
    UserPersonalInfoBase, UserPersonalInfoCreate, UserPersonalInfoUpdate,
    UserPersonalInfoResponse, UserPersonalInfoWithUser
)

# Modelos de plataformas de empleo
from .employment_platforms import (
    PlatformTypeEnum, PlatformCategoryEnum,
    EmploymentPlatformBase, EmploymentPlatformCreate, EmploymentPlatformUpdate,
    EmploymentPlatformResponse, EmploymentPlatformWithStats
)

# Modelos de reseñas
from .reviews import (
    ReviewTypeEnum, ReviewBase, ReviewCreate, ReviewUpdate,
    ReviewResponse, ReviewWithRelations, ReviewStats
)

__all__ = [
    # Auth models
    "UserRegister",
    "UserLogin", 
    "UserResponse",
    "Token",
    "TokenData",
    # Document models
    "DocumentType",
    "DocumentUploadResponse", 
    "DocumentInfo",
    "UserDocumentsResponse",
    "DocumentDeleteResponse",
    "DocumentValidationError",
    "DocumentUploadRequest",
    "UserFolderInfo",
    "DocumentValidator",
    "DocumentErrorResponses",
    # User Profile models
    "GenderEnum",
    "EducationLevelEnum", 
    "DigitalLevelEnum",
    "UserPersonalInfoBase",
    "UserPersonalInfoCreate",
    "UserPersonalInfoUpdate",
    "UserPersonalInfoResponse",
    "UserPersonalInfoWithUser",
    # Employment Platform models
    "PlatformTypeEnum",
    "PlatformCategoryEnum",
    "EmploymentPlatformBase",
    "EmploymentPlatformCreate", 
    "EmploymentPlatformUpdate",
    "EmploymentPlatformResponse",
    "EmploymentPlatformWithStats",
    # Review models
    "ReviewTypeEnum",
    "ReviewBase",
    "ReviewCreate",
    "ReviewUpdate", 
    "ReviewResponse",
    "ReviewWithRelations",
    "ReviewStats"
]