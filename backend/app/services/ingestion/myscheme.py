from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import ApiError
from app.db.models import IngestionRun
from app.schemas.ingestion import MySchemeIngestionRequest, MySchemeIngestionResponse
from app.services.schemes import ensure_organisation


async def start_myscheme_ingestion(db: AsyncSession, request: MySchemeIngestionRequest) -> MySchemeIngestionResponse:
    org = await ensure_organisation(db, request.organisation_id)
    settings = get_settings()
    if request.mode == "api" and not settings.myscheme_api_base_url:
        raise ApiError(
            424,
            "INGESTION_SOURCE_UNAVAILABLE",
            "MyScheme API base URL or credentials are not configured. Use json_file or csv mode.",
            "MYSCHEME_API_BASE_URL",
        )
    run = IngestionRun(
        organisation_id=org.id,
        source="myscheme",
        mode=request.mode,
        status="completed" if request.dry_run else "started",
        source_uri=request.source_uri,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    return MySchemeIngestionResponse(ingestion_run_id=str(run.id), status=run.status)

