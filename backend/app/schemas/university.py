from pydantic import BaseModel


class UniversityResponse(BaseModel):
    id: str
    name: str
    slug: str
    country: str

