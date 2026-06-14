from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.security import hash_password
from app.models.channel import Channel
from app.models.enums import OperationMode, UserRole
from app.models.user import User
from app.services.topic_engine import generate_topic_candidates

settings = get_settings()


async def ensure_pilot_channel(session: AsyncSession) -> Channel:
    result = await session.execute(select(Channel).limit(1))
    channel = result.scalar_one_or_none()
    if channel:
        return channel

    channel = Channel(
        name="파일럿 채널",
        operation_mode=OperationMode(settings.default_operation_mode),
        daily_upload_cap=settings.daily_upload_cap,
        category_allowlist=settings.category_allowlist,
        is_active=True,
    )
    session.add(channel)
    await session.flush()
    return channel


async def ensure_admin_user(session: AsyncSession) -> None:
    result = await session.execute(select(User).where(User.email == settings.admin_email))
    if result.scalar_one_or_none():
        return
    session.add(
        User(
            email=settings.admin_email,
            hashed_password=hash_password(settings.admin_password),
            role=UserRole.ADMIN,
            is_active=True,
        )
    )
    await session.flush()


async def seed_initial_data(session: AsyncSession) -> None:
    await ensure_admin_user(session)
    channel = await ensure_pilot_channel(session)

    from app.models.topic_candidate import TopicCandidate

    result = await session.execute(
        select(TopicCandidate).where(TopicCandidate.channel_id == channel.id).limit(1)
    )
    if result.scalar_one_or_none() is None:
        await generate_topic_candidates(
            session,
            channel.id,
            channel.category_allowlist,
            limit=4,
        )

    await session.commit()
