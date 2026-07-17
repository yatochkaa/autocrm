from __future__ import annotations
from pydantic import BaseModel, Field
class RuntimeSettingsOut(BaseModel):
    auto_priority_enabled: bool
    normal_after_minutes: int
    high_after_minutes: int
    urgent_after_minutes: int
class RuntimeSettingsUpdate(BaseModel):
    auto_priority_enabled: bool
    normal_after_minutes: int=Field(ge=0,le=525600)
    high_after_minutes: int=Field(ge=1,le=525600)
    urgent_after_minutes: int=Field(ge=2,le=525600)
class UserSummary(BaseModel):
    id:int;email:str;username:str;full_name:str;role:str;total_leads:int;active_leads:int
class ManagerCreate(BaseModel):
    full_name:str=Field(min_length=2,max_length=120);username:str=Field(min_length=3,max_length=32);password:str=Field(min_length=8,max_length=72)
class ManagerUpdate(BaseModel):
    full_name:str=Field(min_length=2,max_length=120);username:str=Field(min_length=3,max_length=32);password:str|None=Field(default=None,min_length=8,max_length=72)
