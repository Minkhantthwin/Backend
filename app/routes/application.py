from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query,
    UploadFile,
    File,
    Form,
)
from sqlalchemy.orm import Session
from typing import List, Optional
import math
import os
import uuid
import base64
from pathlib import Path
from datetime import datetime

from app.database import get_mysql_session
from app.repositories.application_repository import ApplicationRepository
from app.schemas import (
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationResponse,
    MessageResponse,
)
from app.util.log import get_logger
from app.dependencies.auth import require_admin, get_current_user

logger = get_logger(__name__)
router = APIRouter()


def get_application_repository(
    db: Session = Depends(get_mysql_session),
) -> ApplicationRepository:
    """Dependency to get application repository"""
    return ApplicationRepository(db)


@router.post(
    "/applications",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new application",
    description="Create a new application for a program",
)
async def create_application(
    application_data: ApplicationCreate,
    application_repo: ApplicationRepository = Depends(get_application_repository),
):
    """
    Create a new application with the following information:

    - **user_id**: ID of the user applying
    - **program_id**: ID of the program being applied to
    - **personal_statement**: Personal statement for the application
    - **additional_documents**: Additional documents (JSON format)
    """
    try:
        application = application_repo.create_application(application_data)
        logger.info(
            f"Application created successfully for user {application_data.user_id}"
        )
        return application

    except ValueError as e:
        logger.warning(f"Application creation failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating application: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while creating application",
        )


@router.get(
    "/applications/stats",
    summary="Application statistics",
    description="Get counts of applications by status (admin only)",
)
async def application_stats(
    application_repo: ApplicationRepository = Depends(get_application_repository),
    current_admin=Depends(require_admin),
):
    try:
        return application_repo.get_status_counts()
    except Exception as e:
        logger.error(f"Unexpected error retrieving application stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error retrieving application stats",
        )


@router.post(
    "/applications/upload-documents",
    summary="Upload application documents",
    description="Upload files for an application and return document metadata",
)
async def upload_application_documents(
    files: List[UploadFile] = File(...),
):
    """
    Upload documents for an application.

    This endpoint accepts multiple files and saves them to the server's
    documents/ folder. It returns path-based metadata that can be stored in
    the application's JSON fields (additional_documents and/or supporting_documents).
    """
    try:
        if not files or len(files) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one document is required",
            )

        # Validate file types and sizes
        allowed_types = {
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "image/jpeg",
            "image/jpg",
            "image/png",
        }
        max_size = 10 * 1024 * 1024  # 10MB

        documents = []
        # Ensure documents folder exists (store under view/documents)
        base_dir = Path(__file__).resolve().parents[2]
        docs_dir = base_dir / "view" / "documents"
        docs_dir.mkdir(parents=True, exist_ok=True)

        for file in files:
            # Validate file type
            if file.content_type not in allowed_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File type {file.content_type} not allowed",
                )

            # Read file content
            content = await file.read()

            # Validate file size
            if len(content) > max_size:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File {file.filename} exceeds maximum size of 10MB",
                )
            # Save to disk with unique name
            doc_id = str(uuid.uuid4())
            safe_name = f"{doc_id}_{file.filename}"
            file_path = docs_dir / safe_name
            with open(file_path, "wb") as f:
                f.write(content)

            # Create document metadata (path based)
            document = {
                "id": doc_id,
                "filename": file.filename,
                "content_type": file.content_type,
                "size": len(content),
                "path": str(file_path.relative_to(base_dir)),
                "uploaded_at": datetime.utcnow().isoformat(),
            }

            documents.append(document)

        logger.info(f"Successfully uploaded {len(documents)} documents")

        return {
            "message": f"Successfully uploaded {len(documents)} documents",
            "documents": documents,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload documents",
        )


@router.post(
    "/applications/with-documents",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create application with document uploads",
    description="Create a new application and upload documents in a single request",
)
async def create_application_with_documents(
    user_id: int = Form(...),
    program_id: int = Form(...),
    personal_statement: str = Form(...),
    academic_background: Optional[str] = Form(None),
    work_experience: Optional[str] = Form(None),
    research_interests: Optional[str] = Form(None),
    additional_info: Optional[str] = Form(None),
    identity_document: Optional[UploadFile] = File(None),
    files: Optional[List[UploadFile]] = File(None),
    application_repo: ApplicationRepository = Depends(get_application_repository),
):
    """
    Create a new application with document uploads.

    This endpoint handles both text data and file uploads in a single request.
    Files are stored on disk under the documents/ folder, and metadata is saved with the application.
    """
    try:
        # Require NRC/Passport and at least one supporting document
        if not identity_document or not getattr(identity_document, "filename", None):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="NRC/Passport document is required",
            )
        if not files or all((not f.filename) for f in files):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one supporting document is required",
            )

        # Prepare additional documents data
        additional_documents = {
            "text_data": {
                "academic_background": academic_background or "",
                "work_experience": work_experience or "",
                "research_interests": research_interests or "",
                "additional_info": additional_info or "",
            },
            "uploaded_files": [],
        }
        supporting_documents = []
        identity_doc_meta = None

        # Process uploaded files
        # Common validation config
        allowed_types = {
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "image/jpeg",
            "image/jpg",
            "image/png",
        }
        max_size = 10 * 1024 * 1024  # 10MB
        base_dir = Path(__file__).resolve().parents[2]

        # Handle identity document (save to view/nrc)
        if identity_document and identity_document.filename:
            if identity_document.content_type not in allowed_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Identity document type {identity_document.content_type} not allowed",
                )
            content = await identity_document.read()
            if len(content) > max_size:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Identity document {identity_document.filename} exceeds maximum size of 10MB",
                )
            nrc_dir = base_dir / "view" / "nrc"
            nrc_dir.mkdir(parents=True, exist_ok=True)
            doc_id = str(uuid.uuid4())
            safe_name = f"{doc_id}_{identity_document.filename}"
            file_path = nrc_dir / safe_name
            with open(file_path, "wb") as f:
                f.write(content)
            identity_doc_meta = {
                "id": doc_id,
                "filename": identity_document.filename,
                "content_type": identity_document.content_type,
                "size": len(content),
                "path": str(file_path.relative_to(base_dir)),
                "uploaded_at": datetime.utcnow().isoformat(),
                "category": "identity",
            }
            additional_documents["identity_document"] = identity_doc_meta
            additional_documents["uploaded_files"].append(identity_doc_meta)

        # Process uploaded supporting files
        if files:
            docs_dir = base_dir / "view" / "documents"
            docs_dir.mkdir(parents=True, exist_ok=True)

            for file in files:
                if file.filename:  # Skip empty file fields
                    # Validate file type
                    if file.content_type not in allowed_types:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"File type {file.content_type} not allowed",
                        )

                    # Read and validate file
                    content = await file.read()
                    if len(content) > max_size:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"File {file.filename} exceeds maximum size of 10MB",
                        )
                    # Save file to disk
                    doc_id = str(uuid.uuid4())
                    safe_name = f"{doc_id}_{file.filename}"
                    file_path = docs_dir / safe_name
                    with open(file_path, "wb") as f:
                        f.write(content)
                    file_data = {
                        "id": doc_id,
                        "filename": file.filename,
                        "content_type": file.content_type,
                        "size": len(content),
                        "path": str(file_path.relative_to(base_dir)),
                        "uploaded_at": datetime.utcnow().isoformat(),
                    }
                    additional_documents["uploaded_files"].append(file_data)
                    supporting_documents.append(file_data)

        # Create application data
        application_data = ApplicationCreate(
            user_id=user_id,
            program_id=program_id,
            personal_statement=personal_statement,
            additional_documents=additional_documents,
            # Fallback: store metadata in additional_documents only to avoid DB column issues
            supporting_documents=None,
        )

        # Create application
        application = application_repo.create_application(application_data)
        logger.info(
            f"Application with {len(additional_documents['uploaded_files'])} documents created for user {user_id}"
        )

        return application

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Application creation failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating application with documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while creating application",
        )


@router.get(
    "/applications/{application_id}",
    response_model=ApplicationResponse,
    summary="Get application by ID",
    description="Retrieve a specific application by its ID",
)
async def get_application(
    application_id: int,
    application_repo: ApplicationRepository = Depends(get_application_repository),
):
    """
    Get a specific application by its ID.

    - **application_id**: The ID of the application to retrieve
    """
    try:
        application = application_repo.get_application_by_id(application_id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Application not found"
            )

        return application

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving application {application_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving application",
        )


@router.get(
    "/users/{user_id}/applications",
    response_model=List[ApplicationResponse],
    summary="Get applications by user",
    description="Retrieve all applications for a specific user",
)
async def get_applications_by_user(
    user_id: int,
    application_repo: ApplicationRepository = Depends(get_application_repository),
):
    """
    Get all applications for a specific user.

    - **user_id**: The ID of the user
    """
    try:
        applications = application_repo.get_applications_by_user(user_id)
        return applications

    except Exception as e:
        logger.error(
            f"Unexpected error retrieving applications for user {user_id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving applications",
        )


@router.get(
    "/programs/{program_id}/applications",
    response_model=List[ApplicationResponse],
    summary="Get applications by program",
    description="Retrieve all applications for a specific program",
)
async def get_applications_by_program(
    program_id: int,
    application_repo: ApplicationRepository = Depends(get_application_repository),
):
    """
    Get all applications for a specific program.

    - **program_id**: The ID of the program
    """
    try:
        applications = application_repo.get_applications_by_program(program_id)
        return applications

    except Exception as e:
        logger.error(
            f"Unexpected error retrieving applications for program {program_id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving applications",
        )


@router.get(
    "/applications",
    response_model=List[ApplicationResponse],
    summary="Get list of applications",
    description="Retrieve a paginated list of applications",
)
async def get_applications(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(
        10, ge=1, le=100, description="Number of applications per page"
    ),
    application_repo: ApplicationRepository = Depends(get_application_repository),
):
    """
    Get a paginated list of applications.

    - **page**: Page number (starts from 1)
    - **per_page**: Number of applications per page (1-100)
    """
    try:
        skip = (page - 1) * per_page

        applications = application_repo.get_applications(skip=skip, limit=per_page)
        return applications

    except Exception as e:
        logger.error(f"Unexpected error retrieving applications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving applications",
        )


@router.put(
    "/applications/{application_id}",
    response_model=ApplicationResponse,
    summary="Update application",
    description="Update application information",
)
async def update_application(
    application_id: int,
    application_data: ApplicationUpdate,
    application_repo: ApplicationRepository = Depends(get_application_repository),
):
    """
    Update application information.

    - **application_id**: The ID of the application to update
    - All fields are optional and only provided fields will be updated
    """
    try:
        application = application_repo.update_application(
            application_id, application_data
        )
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Application not found"
            )

        logger.info(f"Application updated successfully: {application_id}")
        return application

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating application {application_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while updating application",
        )


@router.delete(
    "/applications/{application_id}",
    response_model=MessageResponse,
    summary="Delete application",
    description="Delete a specific application",
)
async def delete_application(
    application_id: int,
    application_repo: ApplicationRepository = Depends(get_application_repository),
):
    """
    Delete a specific application.

    - **application_id**: The ID of the application to delete
    """
    try:
        success = application_repo.delete_application(application_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Application not found"
            )

        logger.info(f"Application deleted: {application_id}")
        return MessageResponse(message="Application deleted successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting application {application_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while deleting application",
        )


@router.get(
    "/applications/{application_id}/documents/{document_id}",
    summary="Download application document",
    description="Download a specific document from an application",
)
async def download_application_document(
    application_id: int,
    document_id: str,
    application_repo: ApplicationRepository = Depends(get_application_repository),
    current_user=Depends(get_current_user),
):
    """
    Download a specific document from an application by reading the file from disk.
    """
    try:
        application = application_repo.get_application_by_id(application_id)
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        # Authorization: owner or admin
        try:
            is_admin = bool(getattr(current_user, "is_admin", False))
            is_owner = int(getattr(current_user, "id", -1)) == int(application.user_id)
        except Exception:
            is_admin = False
            is_owner = False
        if not (is_admin or is_owner):
            raise HTTPException(
                status_code=403, detail="Not enough permissions to access this document"
            )

        # Prefer path-based supporting_documents; fallback to additional_documents.uploaded_files
        candidate_lists = []
        if getattr(application, "supporting_documents", None):
            candidate_lists.append(application.supporting_documents)
        if getattr(application, "additional_documents", None) and isinstance(
            application.additional_documents, dict
        ):
            ul = application.additional_documents.get("uploaded_files")
            if ul:
                candidate_lists.append(ul)

        document = None
        for docs in candidate_lists:
            for doc in docs:
                if str(doc.get("id")) == str(document_id):
                    document = doc
                    break
            if document:
                break

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Resolve path and stream file
        rel_path = document.get("path")
        if not rel_path:
            raise HTTPException(status_code=404, detail="Document path not available")
        base_dir = Path(__file__).resolve().parents[2]
        file_path = (base_dir / rel_path).resolve()
        if not file_path.exists():
            # Fallback: if previously saved under project-root/documents, try mapping to view/documents
            try:
                rel_p = Path(rel_path)
                if rel_p.parts and rel_p.parts[0] != "view":
                    alt_path = (base_dir / "view" / rel_p).resolve()
                    if alt_path.exists():
                        file_path = alt_path
            except Exception:
                pass
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found on server")

        from fastapi.responses import FileResponse

        return FileResponse(
            path=str(file_path),
            media_type=document.get("content_type") or "application/octet-stream",
            filename=document.get("filename") or file_path.name,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error downloading document: {e}")
        raise HTTPException(status_code=500, detail="Failed to download document")
