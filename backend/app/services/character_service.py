"""캐릭터 CRUD + 시드."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.character import Character

DEFAULT_CHARACTERS = [
    {
        "code": "CHR-GRANDMA",
        "name": "순자 할머니",
        "role": "grandmother",
        "speech_style": "따뜻한 존댓말, 쉬운 설명",
        "language_primary": "ko",
        "sort_order": 1,
    },
    {
        "code": "CHR-YOUTH",
        "name": "Jake",
        "role": "youth",
        "speech_style": "밝은 한국어, 가끔 영어 질문",
        "language_primary": "ko",
        "sort_order": 2,
    },
]


async def next_character_code(session: AsyncSession) -> str:
    result = await session.execute(select(func.count()).select_from(Character))
    count = result.scalar() or 0
    return f"CHR-{count + 1:03d}"


async def ensure_default_characters(session: AsyncSession) -> None:
    result = await session.execute(select(Character).limit(1))
    if result.scalar_one_or_none():
        return
    for item in DEFAULT_CHARACTERS:
        session.add(Character(**item))
    await session.flush()


async def list_characters(session: AsyncSession, active_only: bool = True) -> list[Character]:
    q = select(Character).order_by(Character.sort_order, Character.name)
    if active_only:
        q = q.where(Character.is_active.is_(True))
    result = await session.execute(q)
    return list(result.scalars().all())


async def get_characters_by_codes(session: AsyncSession, codes: list[str]) -> dict[str, Character]:
    if not codes:
        return {}
    result = await session.execute(select(Character).where(Character.code.in_(codes)))
    chars = result.scalars().all()
    return {c.code: c for c in chars}


async def get_characters_by_roles(session: AsyncSession, roles: list[str]) -> list[Character]:
    result = await session.execute(
        select(Character).where(Character.role.in_(roles), Character.is_active.is_(True))
    )
    return list(result.scalars().all())
