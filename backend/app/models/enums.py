import enum


class OperationMode(str, enum.Enum):
    MANUAL = "manual"
    SEMI_AUTO = "semi_auto"
    AUTO = "auto"


class TopicStatus(str, enum.Enum):
    GENERATED = "generated"
    RECOMMENDED = "recommended"
    REVIEW_REQUIRED = "review_required"
    ON_HOLD = "on_hold"
    REJECTED = "rejected"
    APPROVED = "approved"


class CopyrightRisk(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class JobStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    TOPIC_APPROVED = "TOPIC_APPROVED"
    SCRIPT_GENERATING = "SCRIPT_GENERATING"
    SCRIPT_READY = "SCRIPT_READY"
    SCRIPT_APPROVED = "SCRIPT_APPROVED"
    TTS_QUEUED = "TTS_QUEUED"
    TTS_PROCESSING = "TTS_PROCESSING"
    TTS_READY = "TTS_READY"
    ASSET_SEARCHING = "ASSET_SEARCHING"
    ASSET_READY = "ASSET_READY"
    RIGHTS_CHECKING = "RIGHTS_CHECKING"
    RIGHTS_PASSED = "RIGHTS_PASSED"
    RIGHTS_HOLD = "RIGHTS_HOLD"
    MANIFEST_BUILDING = "MANIFEST_BUILDING"
    RENDER_QUEUED = "RENDER_QUEUED"
    RENDER_PROCESSING = "RENDER_PROCESSING"
    RENDER_READY = "RENDER_READY"
    SUBTITLE_PROCESSING = "SUBTITLE_PROCESSING"
    SUBTITLE_READY = "SUBTITLE_READY"
    THUMBNAIL_READY = "THUMBNAIL_READY"
    METADATA_CHECKING = "METADATA_CHECKING"
    METADATA_APPROVED = "METADATA_APPROVED"
    QA_PENDING = "QA_PENDING"
    QA_APPROVED = "QA_APPROVED"
    QA_HOLD = "QA_HOLD"
    UPLOAD_QUEUED = "UPLOAD_QUEUED"
    UPLOADING = "UPLOADING"
    UPLOADED = "UPLOADED"
    UPLOAD_FAILED = "UPLOAD_FAILED"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"
    CANCELLED = "CANCELLED"


class StageStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    HOLD = "hold"


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    OPERATOR = "operator"
    AUDITOR = "auditor"
