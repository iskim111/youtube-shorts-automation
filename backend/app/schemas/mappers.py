from app.models.channel import Channel
from app.models.job import Job
from app.models.topic_candidate import TopicCandidate
from app.schemas.channel import ChannelResponse
from app.schemas.job import JobDetailResponse, JobStageResponse, JobSummaryResponse
from app.schemas.topic import TopicCandidateResponse, TopicScores


def topic_to_response(topic: TopicCandidate) -> TopicCandidateResponse:
    return TopicCandidateResponse(
        id=topic.code,
        category=topic.category,
        keyword_cluster=topic.keyword_cluster,
        hook_line=topic.hook_line,
        scores=TopicScores(
            view_potential=float(topic.score_view_potential),
            competition=float(topic.score_competition),
            production=float(topic.score_production),
            copyright_safety=float(topic.score_copyright_safety),
            final=float(topic.score_final),
        ),
        copyright_risk=topic.copyright_risk.value,
        ai_label_required=topic.ai_label_required,
        status=topic.status.value,
    )


def channel_to_response(channel: Channel) -> ChannelResponse:
    oauth = channel.oauth_credential
    return ChannelResponse(
        id=str(channel.id),
        name=channel.name,
        operation_mode=channel.operation_mode.value,
        daily_upload_cap=channel.daily_upload_cap,
        category_allowlist=channel.category_allowlist,
        is_active=channel.is_active,
        youtube_channel_id=channel.youtube_channel_id,
        oauth_connected=oauth is not None,
        youtube_channel_title=oauth.youtube_channel_title if oauth else None,
    )


def job_to_summary(job: Job) -> JobSummaryResponse:
    topic = job.topic_candidate
    return JobSummaryResponse(
        id=job.code,
        channel_name=job.channel.name if job.channel else "",
        status=job.status.value,
        topic_score=float(topic.score_final) if topic else 0,
        hook_line=topic.hook_line if topic else "",
    )


def job_to_detail(job: Job) -> JobDetailResponse:
    topic = job.topic_candidate
    upload = job.upload_record
    return JobDetailResponse(
        id=job.code,
        channel_name=job.channel.name if job.channel else "",
        status=job.status.value,
        operation_mode=job.operation_mode.value,
        topic_score=float(topic.score_final) if topic else 0,
        hook_line=topic.hook_line if topic else "",
        stages=[
            JobStageResponse(stage=s.stage, status=s.status.value, output_uri=s.output_uri)
            for s in sorted(job.stages, key=lambda x: x.created_at)
        ],
        hold_reason=job.hold_reason,
        script=job.script.content if job.script else None,
        youtube_video_id=upload.youtube_video_id if upload else None,
        upload_dry_run=upload.upload_status == "dry_run" if upload else None,
        metadata_title=upload.title if upload else None,
        render_template=job.render_template or "bold_center",
        scheduled_publish_at=job.scheduled_publish_at,
        assets=[
            {
                "source_type": a.source_type,
                "license_status": a.license_status,
                "source_url": a.source_url,
            }
            for a in (job.assets or [])
        ],
    )
