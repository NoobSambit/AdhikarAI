from uuid import UUID

from app.schemas.agent import HouseholdMemberProfileModel


class CreateHouseholdMemberRequest(HouseholdMemberProfileModel):
    organisation_id: UUID
    id: None = None
