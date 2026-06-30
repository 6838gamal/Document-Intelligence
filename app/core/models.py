from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    REVIEWER = "reviewer"
    VIEWER = "viewer"


class DocumentStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    REVIEWED = "reviewed"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class WorkflowStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200), unique=True, index=True, nullable=False)
    hashed_password = Column(String(500), nullable=False)
    role = Column(String(50), default=UserRole.VIEWER)
    department = Column(String(200))
    avatar = Column(String(500))
    is_active = Column(Boolean, default=True)
    language = Column(String(10), default="ar")
    theme = Column(String(10), default="light")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    documents = relationship("Document", back_populates="uploader")
    approvals = relationship("Approval", back_populates="approver")
    audit_logs = relationship("AuditLog", back_populates="user")


class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    file_name = Column(String(500), nullable=False)
    file_type = Column(String(50))
    file_size = Column(Integer)
    file_path = Column(String(1000))
    status = Column(String(50), default=DocumentStatus.UPLOADED)
    category = Column(String(200))
    tags = Column(JSON, default=list)
    extracted_data = Column(JSON, default=dict)
    confidence_score = Column(Float, default=0.0)
    language = Column(String(10), default="ar")
    page_count = Column(Integer, default=1)
    summary = Column(Text)
    uploader_id = Column(Integer, ForeignKey("users.id"))
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    uploader = relationship("User", back_populates="documents")
    approvals = relationship("Approval", back_populates="document")
    project = relationship("Project", back_populates="documents")


class Approval(Base):
    __tablename__ = "approvals"
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    approver_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String(50), default=ApprovalStatus.PENDING)
    notes = Column(Text)
    due_date = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    priority = Column(String(20), default="normal")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    document = relationship("Document", back_populates="approvals")
    approver = relationship("User", back_populates="approvals")


class Workflow(Base):
    __tablename__ = "workflows"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(String(50), default=WorkflowStatus.DRAFT)
    trigger_type = Column(String(100))
    nodes = Column(JSON, default=list)
    edges = Column(JSON, default=list)
    category = Column(String(100))
    run_count = Column(Integer, default=0)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="active")
    progress = Column(Integer, default=0)
    client = Column(String(200))
    budget = Column(Float)
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    manager_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    documents = relationship("Document", back_populates="project")


class Vendor(Base):
    __tablename__ = "vendors"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    code = Column(String(50))
    category = Column(String(100))
    contact_name = Column(String(200))
    email = Column(String(200))
    phone = Column(String(50))
    country = Column(String(100))
    city = Column(String(100))
    status = Column(String(50), default="active")
    rating = Column(Float, default=0.0)
    contract_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    company = Column(String(200))
    email = Column(String(200))
    phone = Column(String(50))
    country = Column(String(100))
    sector = Column(String(100))
    status = Column(String(50), default="active")
    contract_value = Column(Float, default=0.0)
    document_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class KnowledgeArticle(Base):
    __tablename__ = "knowledge_articles"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    collection = Column(String(200))
    tags = Column(JSON, default=list)
    author_id = Column(Integer, ForeignKey("users.id"))
    view_count = Column(Integer, default=0)
    is_published = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(500), nullable=False)
    message = Column(Text)
    type = Column(String(50), default="info")
    is_read = Column(Boolean, default=False)
    action_url = Column(String(1000))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(200), nullable=False)
    resource_type = Column(String(100))
    resource_id = Column(String(100))
    before_data = Column(JSON)
    after_data = Column(JSON)
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="audit_logs")
