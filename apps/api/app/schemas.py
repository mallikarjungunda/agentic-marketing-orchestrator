from typing import Literal
from pydantic import BaseModel, Field

class CampaignBrief(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    audience: str = Field(min_length=3, max_length=300)
    objective: str = Field(min_length=10, max_length=2000)

class Plan(BaseModel):
    steps: list[str] = Field(min_length=1, max_length=8)

class Draft(BaseModel):
    subject: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=8000)

class Review(BaseModel):
    passed: bool
    findings: list[str]

class Decision(BaseModel):
    version: int = Field(ge=1)
    decision: Literal['approve', 'reject']
