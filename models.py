
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, CheckConstraint, Column, DateTime, ForeignKey, Index,
    Integer, JSON, String, Table, Text, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_code", ForeignKey("roles.code", ondelete="RESTRICT"), primary_key=True),
    Column(
        "assigned_at",
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
)


class Role(Base):
    __tablename__ = "roles"

    code: Mapped[str] = mapped_column(String(30), primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    users: Mapped[list["User"]] = relationship(
        secondary=user_roles,
        back_populates="roles"
    )


class AssessmentDefinition(Base):
    __tablename__ = "assessment_definitions"
    __table_args__ = (
        Index("ix_assessment_definitions_status_category", "status", "category"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    category: Mapped[str] = mapped_column(
        String(100), nullable=False, default="General"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="published"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    questions: Mapped[list["Question"]] = relationship(
        back_populates="assessment",
        order_by="Question.sort_order",
        passive_deletes=True
    )
    attempts: Mapped[list["LearnerAssessmentAttempt"]] = relationship(
        back_populates="assessment"
    )


class Question(Base):
    __tablename__ = "questions"
    __table_args__ = (
        Index("ix_questions_assessment_order", "assessment_id", "sort_order"),
        Index("ix_questions_category", "category"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    assessment_id: Mapped[int | None] = mapped_column(
        ForeignKey("assessment_definitions.id", ondelete="SET NULL"),
        nullable=True
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[list] = mapped_column(JSON, nullable=False)
    correct_answer: Mapped[int] = mapped_column(Integer, nullable=False)
    question_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="single_choice"
    )
    explanation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    category: Mapped[str] = mapped_column(
        String(100), nullable=False, default="General"
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    assessment: Mapped[AssessmentDefinition | None] = relationship(
        back_populates="questions"
    )
    legacy_answers: Mapped[list["AssessmentAnswer"]] = relationship(
        back_populates="question"
    )


class Article(Base):
    __tablename__ = "knowledge_articles"
    __table_args__ = (
        Index(
            "ix_knowledge_articles_published_category",
            "published",
            "category"
        ),
        Index(
            "ix_knowledge_articles_resource_published",
            "resource_type",
            "published"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    keywords: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    resource_type: Mapped[str] = mapped_column(
        String(30), default="article"
    )
    difficulty: Mapped[str] = mapped_column(
        String(30), default="Beginner", nullable=False
    )
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    video_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    views_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    saves_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    featured: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    published: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    author: Mapped["User | None"] = relationship(back_populates="articles")
    bookmarks: Mapped[list["Bookmark"]] = relationship(
        back_populates="article",
        cascade="all, delete-orphan",
        passive_deletes=True
    )


class Assessment(Base):
    """Legacy assessment-result table retained for existing database rows."""

    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    total_questions: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    answers: Mapped[list["AssessmentAnswer"]] = relationship(
        back_populates="assessment",
        cascade="all, delete-orphan",
        passive_deletes=True
    )


class AssessmentAnswer(Base):
    __tablename__ = "assessment_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    assessment_id: Mapped[int] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id"),
        nullable=False
    )
    selected_answer: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    assessment: Mapped[Assessment] = relationship(back_populates="answers")
    question: Mapped[Question] = relationship(back_populates="legacy_answers")


class LearnerAssessmentAttempt(Base):
    __tablename__ = "learner_assessment_attempts"
    __table_args__ = (
        Index(
            "uq_learner_assessment_user_token",
            "user_id",
            "attempt_token",
            unique=True
        ),
        Index("ix_learner_assessment_user_completed", "user_id", "completed_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    assessment_id: Mapped[int | None] = mapped_column(
        ForeignKey("assessment_definitions.id", ondelete="SET NULL"),
        nullable=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    attempt_token: Mapped[str] = mapped_column(String(36), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    percentage: Mapped[float | None] = mapped_column(nullable=True)
    category_breakdown: Mapped[list] = mapped_column(JSON, nullable=False)
    answer_review: Mapped[list] = mapped_column(JSON, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    user: Mapped["User"] = relationship(back_populates="assessment_attempts")
    assessment: Mapped[AssessmentDefinition | None] = relationship(
        back_populates="attempts"
    )
    normalized_answers: Mapped[list["AssessmentAttemptAnswer"]] = relationship(
        back_populates="learner_attempt",
        cascade="all, delete-orphan",
        passive_deletes=True
    )


class ResearchAssessmentResponse(Base):
    __tablename__ = "research_assessment_responses"
    __table_args__ = (
        Index("ix_research_responses_status_started", "status", "started_at"),
        Index("ix_research_responses_assessment_started", "assessment_code", "started_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    assessment_id: Mapped[int | None] = mapped_column(
        ForeignKey("assessment_definitions.id", ondelete="SET NULL"),
        nullable=True
    )
    participant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    assessment_code: Mapped[str] = mapped_column(
        String(80), default="general-nursing-knowledge", nullable=False
    )
    protocol_id: Mapped[str] = mapped_column(String(120), nullable=False)
    consented: Mapped[bool] = mapped_column(Boolean, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="started", nullable=False
    )
    progress_answers: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_questions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    answers: Mapped[list | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    assessment: Mapped[AssessmentDefinition | None] = relationship()
    normalized_answers: Mapped[list["AssessmentAttemptAnswer"]] = relationship(
        back_populates="research_response",
        cascade="all, delete-orphan",
        passive_deletes=True
    )


class ResearchAuditLog(Base):
    __tablename__ = "research_audit_logs"
    __table_args__ = (
        Index("ix_research_audit_actor_created", "actor_user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(40), nullable=False)
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    actor: Mapped["User"] = relationship(
        back_populates="research_audit_logs"
    )


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_email", "email", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(20), default="learner", nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    roles: Mapped[list[Role]] = relationship(
        secondary=user_roles,
        back_populates="users"
    )
    assessment_attempts: Mapped[list[LearnerAssessmentAttempt]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    articles: Mapped[list[Article]] = relationship(back_populates="author")
    sessions: Mapped[list["AuthSession"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    research_audit_logs: Mapped[list[ResearchAuditLog]] = relationship(
        back_populates="actor"
    )
    tutor_usage: Mapped[list["AITutorUsage"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    discussion_posts: Mapped[list["DiscussionPost"]] = relationship(
        back_populates="author",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    bookmarks: Mapped[list["Bookmark"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True
    )


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    user: Mapped[User] = relationship(back_populates="sessions")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    __table_args__ = (
        Index(
            "ix_password_reset_tokens_user_created",
            "user_id",
            "created_at"
        ),
    )

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    user: Mapped[User] = relationship()


class AuthRateLimitEvent(Base):
    __tablename__ = "auth_rate_limit_events"
    __table_args__ = (
        Index(
            "ix_auth_rate_limit_identifier_action_created",
            "identifier_hash",
            "action",
            "created_at"
        ),
        Index(
            "ix_auth_rate_limit_ip_action_created",
            "ip_hash",
            "action",
            "created_at"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    identifier_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    ip_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )


class AITutorUsage(Base):
    __tablename__ = "ai_tutor_usage"
    __table_args__ = (
        Index("ix_ai_tutor_usage_user_created", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    user: Mapped[User] = relationship(back_populates="tutor_usage")


class QuestionBankItem(Base):
    __tablename__ = "question_bank_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[list] = mapped_column(JSON, nullable=False)
    correct_answer: Mapped[int] = mapped_column(Integer, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    source_url: Mapped[str] = mapped_column(String(500), nullable=False)


class DiscussionPost(Base):
    __tablename__ = "discussion_posts"
    __table_args__ = (
        Index("ix_discussion_posts_status_created", "status", "created_at"),
        Index("ix_discussion_posts_author_created", "author_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    author: Mapped[User] = relationship(back_populates="discussion_posts")


class AssessmentAttemptAnswer(Base):
    __tablename__ = "assessment_attempt_answers"
    __table_args__ = (
        CheckConstraint(
            "(learner_attempt_id IS NOT NULL AND research_response_id IS NULL) "
            "OR (learner_attempt_id IS NULL AND research_response_id IS NOT NULL)",
            name="ck_attempt_answer_single_parent"
        ),
        UniqueConstraint(
            "learner_attempt_id",
            "question_id",
            name="uq_learner_attempt_question_answer"
        ),
        UniqueConstraint(
            "research_response_id",
            "question_id",
            name="uq_research_response_question_answer"
        ),
        Index("ix_attempt_answers_question", "question_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    learner_attempt_id: Mapped[int | None] = mapped_column(
        ForeignKey("learner_assessment_attempts.id", ondelete="CASCADE"),
        nullable=True
    )
    research_response_id: Mapped[str | None] = mapped_column(
        ForeignKey("research_assessment_responses.id", ondelete="CASCADE"),
        nullable=True
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="RESTRICT"),
        nullable=False
    )
    selected_answer: Mapped[int] = mapped_column(Integer, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    learner_attempt: Mapped[LearnerAssessmentAttempt | None] = relationship(
        back_populates="normalized_answers"
    )
    research_response: Mapped[ResearchAssessmentResponse | None] = relationship(
        back_populates="normalized_answers"
    )
    question: Mapped[Question] = relationship()


class Bookmark(Base):
    __tablename__ = "bookmarks"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "resource_type",
            "resource_id",
            name="uq_bookmark_user_resource"
        ),
        Index("ix_bookmarks_user_created", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    resource_type: Mapped[str] = mapped_column(String(30), nullable=False)
    resource_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_articles.id", ondelete="CASCADE"),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    user: Mapped[User] = relationship(back_populates="bookmarks")
    article: Mapped[Article] = relationship(back_populates="bookmarks")


class EmergencyResource(Base):
    __tablename__ = "emergency_resources"
    __table_args__ = (
        Index("ix_emergency_resources_category", "category"),
        Index("ix_emergency_resources_updated", "updated_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    references_json: Mapped[list[str]] = mapped_column(
        "references", JSON, nullable=False, default=list
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )


class NursingTool(Base):
    __tablename__ = "nursing_tools"
    __table_args__ = (
        Index("ix_nursing_tools_type", "tool_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    tool_type: Mapped[str] = mapped_column(String(40), nullable=False)
    configuration: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
