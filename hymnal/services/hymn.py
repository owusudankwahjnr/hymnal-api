from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func, String, and_, cast, exists
from fastapi import HTTPException, UploadFile
from hymnal.models.hymn_book import HymnBook
from hymnal.models.hymn import Hymn
from hymnal.schemas.hymn import HymnSearchResult
from user_management.services.user import log_action
from typing import Dict, List, Optional
import aiofiles
import os
import uuid

# Base directory for media files
MEDIA_DIR = "media/hymn_books/thumbnails"

# Ensure media directory exists (synchronous, run at startup)
os.makedirs(MEDIA_DIR, exist_ok=True)


async def create_hymn_book(db: AsyncSession, hymn_book: "HymnBookCreate", user_id: str) -> HymnBook:
    db_hymn_book = HymnBook(**hymn_book.dict())
    db.add(db_hymn_book)
    await db.commit()
    await db.refresh(db_hymn_book)
    await log_action(db, user_id, "CREATE_HYMN_BOOK", f"Created hymn book {hymn_book.title}")
    return db_hymn_book


async def update_hymn_book_thumbnail(db: AsyncSession, hymn_book_id: str, thumbnail: UploadFile,
                                     user_id: str) -> HymnBook:

    result = await db.execute(select(HymnBook).filter(HymnBook.id == hymn_book_id))
    hymn_book = result.scalars().first()
    if not hymn_book:
        raise HTTPException(status_code=404, detail="Hymn book not found")
    if thumbnail.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Invalid image format")

    # Generate unique filename
    file_extension = thumbnail.filename.split(".")[-1]
    filename = f"book_{hymn_book_id}_{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(MEDIA_DIR, filename)

    # Save file asynchronously
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(await thumbnail.read())

    # Delete old thumbnail if exists
    if hymn_book.thumbnail_path and os.path.exists(hymn_book.thumbnail_path):
        os.remove(hymn_book.thumbnail_path)  # Synchronous, as aiofiles.delete is not critical

    # Update path
    hymn_book.thumbnail_path = file_path
    await db.commit()
    await db.refresh(hymn_book)
    await log_action(db, user_id, "UPDATE_HYMN_BOOK_THUMBNAIL",
                     f"Updated thumbnail for hymn book {hymn_book.title}")
    return hymn_book


async def create_hymn(db: AsyncSession, hymn: "HymnCreate", user_id: str) -> Hymn:

    result = await db.execute(select(HymnBook).filter(HymnBook.id == hymn.hymn_book_id))
    hymn_book = result.scalars().first()
    if not hymn_book:
        raise HTTPException(status_code=404, detail="Hymn book not found")
    validate_hymn_content(hymn.content)  # Synchronous validation, as it's CPU-bound
    db_hymn = Hymn(**hymn.dict())
    db.add(db_hymn)
    await db.commit()
    await db.refresh(db_hymn)
    await log_action(db, user_id, "CREATE_HYMN", f"Created hymn {hymn.title} in book {hymn_book.title}")
    return db_hymn


async def get_hymn_book(db: AsyncSession, hymn_book_id: str) -> HymnBook:
    result = await db.execute(select(HymnBook).filter(HymnBook.id == hymn_book_id))
    return result.scalars().first()


async def get_all_hymn_books(db: AsyncSession) -> List[HymnBook]:
    result = await db.execute(select(HymnBook).order_by(HymnBook.title.asc()))
    return result.scalars().all()


async def get_hymn(db: AsyncSession, hymn_id: str) -> Hymn:
    result = await db.execute(select(Hymn).filter(Hymn.id == hymn_id))
    return result.scalars().first()


async def update_hymn(db: AsyncSession, hymn_id: str, hymn: "HymnUpdate", user_id: str) -> Hymn:
    async with db.begin():
        result = await db.execute(select(Hymn).filter(Hymn.id == hymn_id))
        db_hymn = result.scalars().first()
        if not db_hymn:
            raise HTTPException(status_code=404, detail="Hymn not found")
        result = await db.execute(select(HymnBook).filter(HymnBook.id == db_hymn.hymn_book_id))
        hymn_book = result.scalars().first()
        if not hymn_book:
            raise HTTPException(status_code=404, detail="Hymn book not found")
        validate_hymn_content(hymn.content)
        for key, value in hymn.dict(exclude_unset=True).items():
            setattr(db_hymn, key, value)
        await db.commit()
        await db.refresh(db_hymn)
        await log_action(db, user_id, "UPDATE_HYMN", f"Updated hymn {hymn.title} in book {hymn_book.title}")
        return db_hymn


async def delete_hymn(db: AsyncSession, hymn_id: str, user_id: str) -> Hymn:
    async with db.begin():
        result = await db.execute(select(Hymn).filter(Hymn.id == hymn_id))
        db_hymn = result.scalars().first()
        if db_hymn:
            result = await db.execute(select(HymnBook).filter(HymnBook.id == db_hymn.hymn_book_id))
            hymn_book = result.scalars().first()
            await db.delete(db_hymn)
            await db.commit()
            await log_action(db, user_id, "DELETE_HYMN", f"Deleted hymn {db_hymn.title} in book {hymn_book.title}")
            return db_hymn
        raise HTTPException(status_code=404, detail="Hymn not found")


async def delete_hymn_book(db: AsyncSession, hymn_book_id: str, user_id: str) -> HymnBook:
    async with db.begin():
        result = await db.execute(select(HymnBook).filter(HymnBook.id == hymn_book_id))
        hymn_book = result.scalars().first()
        if not hymn_book:
            raise HTTPException(status_code=404, detail="Hymn book not found")
        if hymn_book.thumbnail_path and os.path.exists(hymn_book.thumbnail_path):
            os.remove(hymn_book.thumbnail_path)  # Synchronous, as aiofiles.delete is not critical
        await db.delete(hymn_book)
        await db.commit()
        await log_action(db, user_id, "DELETE_HYMN_BOOK", f"Deleted hymn book {hymn_book.title}")
        return hymn_book


async def get_hymns_by_hymn_book_id(
    db: AsyncSession, hymn_book_id: str, skip: int = 0, limit: int = 10
) -> List[HymnSearchResult]:
    result = await db.execute(
        select(Hymn, HymnBook.title.label("hymn_book_title"))
        .join(HymnBook)
        .filter(Hymn.hymn_book_id == hymn_book_id)
        .offset(skip)
        .limit(limit)
    )
    results = result.all()
    return [
        HymnSearchResult(
            id=hymn.id,
            title=hymn.title,
            number=hymn.number,
            hymn_book_id=hymn.hymn_book_id,
            hymn_book_title=hymn_book_title,
            variant_key=hymn.variant_key,
        )
        for hymn, hymn_book_title in results
    ]


async def search_hymns_by_filters(
    db: AsyncSession,
    title: Optional[str] = None,
    number: Optional[int] = None,
    hymn_book_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
) -> List[HymnSearchResult]:
    query = select(Hymn, HymnBook.title.label("hymn_book_title")).join(HymnBook)

    filters = []
    is_asc = False
    if title is not None:
        # ilike for title (case-insensitive partial match)
        title_filter = Hymn.title.ilike(f"%{title}%")

        # ilike for number (cast number to string for partial numeric match)
        number_filter = cast(Hymn.number, String).ilike(f"%{title}%")

        # combine both
        filters.append(or_(title_filter, number_filter))
    if number is not None:
        filters.append(Hymn.number == number)
    if hymn_book_id is not None:
        filters.append(Hymn.hymn_book_id == hymn_book_id)

    if filters:
        query = query.filter(and_(*filters))

    if hymn_book_id:
        query = query.order_by(Hymn.number.asc())
        is_asc = True

    # If title is purely numeric, order by number ascending
    if title and title.isdigit():
        if not is_asc:
            query = query.order_by(Hymn.number.asc())

    result = await db.execute(query.offset(skip).limit(limit))
    results = result.all()

    if not results and title:
        try:
            # Fallback: Search in content (any verse_content or chorus)
            content_query = select(Hymn, HymnBook.title.label("hymn_book_title")).join(HymnBook)

            # Chorus filter (assuming chorus is a string)
            chorus_filter = cast(Hymn.content.op('->>')('chorus'), String).ilike(f"%{title}%")

            # Verses filter (any verse_content in the array) - Use json_array_elements for JSON type
            verses_elem = func.json_array_elements(Hymn.content.op('->')('verses')).alias('verse_elem')
            verses_subquery = (
                select(1)
                .select_from(verses_elem)
                .where(cast(verses_elem.c.verse_elem.op('->>')('verse_content'), String).ilike(f"%{title}%"))
            )
            verses_filter = exists(verses_subquery)

            content_filters = [or_(chorus_filter, verses_filter)]
            if hymn_book_id is not None:
                content_filters.append(Hymn.hymn_book_id == hymn_book_id)

            content_query = content_query.filter(and_(*content_filters))
            content_result = await db.execute(content_query.offset(skip).limit(limit))
            results = content_result.all()

        except AttributeError:
            pass

    return [
        HymnSearchResult(
            id=hymn.id,
            title=hymn.title,
            number=hymn.number,
            hymn_book_id=hymn.hymn_book_id,
            hymn_book_title=hymn_book_title,
            variant_key=hymn.variant_key,
        )
        for hymn, hymn_book_title in results
    ]


async def get_hymn_variants(db: AsyncSession, hymn_id: str) -> List[Dict]:
    async with db.begin():
        result = await db.execute(select(Hymn).filter(Hymn.id == hymn_id))
        hymn = result.scalars().first()
        if not hymn:
            raise HTTPException(status_code=404, detail="Hymn not found")
        if hymn.variant_key:
            result = await db.execute(
                select(Hymn, HymnBook.title.label("hymn_book_title"))
                .join(HymnBook)
                .filter(Hymn.variant_key == hymn.variant_key, Hymn.id != hymn_id)
            )
        else:
            result = await db.execute(
                select(Hymn, HymnBook.title.label("hymn_book_title"))
                .join(HymnBook)
                .filter(Hymn.title.ilike(f"%{hymn.title}%"), Hymn.id != hymn_id)
            )
        variants = result.all()
        return [
            {
                "id": variant.id,
                "title": variant.title,
                "number": variant.number,
                "hymn_book_id": variant.hymn_book_id,
                "hymn_book_title": hymn_book_title,
                "variant_key": variant.variant_key,
            }
            for variant, hymn_book_title in variants
        ]


def validate_hymn_content(content: Dict):
    # Synchronous, as it's CPU-bound
    verses = content.get("verses", [])
    if not verses or not isinstance(verses, list) or len(verses) < 1:
        raise HTTPException(status_code=400, detail="Hymn must have at least one verse")
    for verse in verses:
        if not all(key in verse for key in ["verse_tag", "verse_name", "verse_content"]):
            raise HTTPException(status_code=400, detail="Each verse must have verse_tag, verse_name, and verse_content")
        if not all(isinstance(verse[key], str) for key in ["verse_tag", "verse_name", "verse_content"]):
            raise HTTPException(status_code=400, detail="verse_tag, verse_name, and verse_content must be strings")

    if "chorus" in content and not isinstance(content["chorus"], str):
        raise HTTPException(status_code=400, detail="Chorus must be a string")