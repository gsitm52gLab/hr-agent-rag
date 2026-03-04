from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class Source(BaseModel):
    document: str
    section: str
    content: str
    score: float


class ChatMessage(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    sources: Optional[list[Source]] = None
    created_at: datetime


class Conversation(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationDetail(BaseModel):
    conversation: Conversation
    messages: list[ChatMessage]


class GlossaryItem(BaseModel):
    id: Optional[int] = None
    term: str
    definition: str
    category: Optional[str] = None
    aliases: Optional[str] = ""
    created_at: Optional[datetime] = None


class GlossaryCreate(BaseModel):
    term: str
    definition: str
    category: Optional[str] = None
    aliases: Optional[str] = ""


class GlossaryUpdate(BaseModel):
    term: Optional[str] = None
    definition: Optional[str] = None
    category: Optional[str] = None
    aliases: Optional[str] = None


class DocumentInfo(BaseModel):
    id: str
    filename: str
    title: str
    content: str
    created_at: Optional[datetime] = None


class DocumentCreate(BaseModel):
    filename: str
    title: str
    content: str


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class SearchStats(BaseModel):
    total_queries: int
    avg_response_time_ms: float
    top_queries: list[dict]
    daily_stats: list[dict]


class RecentSearch(BaseModel):
    id: int
    query: str
    created_at: datetime


class ExampleQuestion(BaseModel):
    id: int
    question: str
    category: Optional[str] = ""
    keywords: Optional[str] = ""


class Department(BaseModel):
    id: int
    name: str
    description: Optional[str] = ""
    parent_id: Optional[int] = None
    sort_order: Optional[int] = 0


class Employee(BaseModel):
    id: int
    name: str
    department_id: int
    position: Optional[str] = ""
    role: Optional[str] = ""
    email: Optional[str] = ""
    phone: Optional[str] = ""
    is_department_head: Optional[bool] = False


class EmployeeCreate(BaseModel):
    name: str
    department_id: int
    position: Optional[str] = ""
    role: Optional[str] = ""
    email: Optional[str] = ""
    phone: Optional[str] = ""
    is_department_head: Optional[bool] = False


class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    department_id: Optional[int] = None
    position: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_department_head: Optional[bool] = None


class OrgChart(BaseModel):
    departments: list[Department]
    employees: list[Employee]
