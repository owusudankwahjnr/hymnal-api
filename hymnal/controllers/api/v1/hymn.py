from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from core.dependencies import get_db, check_permission
from user_management.schemas.user import UserOut
from hymnal.schemas.hymn import (
    HymnBookCreate, HymnBookOut,
    HymnCreate, HymnOut, HymnUpdate,
    HymnSearchResult, HymnVariantResult, HymnFilterParams
)
from hymnal.services.hymn import (
    create_hymn_book, update_hymn_book_thumbnail, delete_hymn_book,
    create_hymn, get_hymn, update_hymn, delete_hymn, get_hymn_variants, get_hymn_book, get_all_hymn_books, search_hymns_by_filters,
    get_hymns_by_hymn_book_id
)

router = APIRouter(
    prefix="/api/v1/hymnal",
    tags=["Hymnal"],
)

@router.post(
    "/hymn_books",
    response_model=HymnBookOut,
    summary="Create a new hymn book",
    description="""
    Create a new hymn book.
- **hymn_book**: Hymn book details (title).
- Requires authentication and `create_hymn_book` permission.
    """,
    response_description="The created hymn book",
)
async def create_hymn_book_endpoint(
    hymn_book: HymnBookCreate = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: UserOut = Depends(check_permission("create_hymn_book")),
):
    return await create_hymn_book(db, hymn_book, current_user.id)

@router.get(
    "/hymn_books",
    response_model=List[HymnBookOut],
    summary="Get all hymn books",
    description="""
    Retrieve a list of all available hymn books.
- Public endpoint (no authentication required).
    """,
    response_description="List of hymn books",
)
async def read_all_hymn_books(
    db: AsyncSession = Depends(get_db),
):
    hymn_books = await get_all_hymn_books(db)
    return hymn_books

@router.get(
    "/hymn_books/{hymn_book_id}",
    response_model=HymnBookOut,
    summary="Get a hymn book by ID",
    description="""
    Retrieve a single hymn book and its details.
- **hymn_book_id**: The unique ID of the hymn book.
- Public endpoint (no authentication required).
    """,
    response_description="The hymn book object",
)
async def read_hymn_book_by_id(
    hymn_book_id: str,
    db: AsyncSession = Depends(get_db),
):
    hymn_book = await get_hymn_book(db, hymn_book_id)
    if not hymn_book:
        raise HTTPException(status_code=404, detail="Hymn book not found")
    return hymn_book


@router.post(
    "/hymn_books/{hymn_book_id}/thumbnail",
    summary="Upload hymn book thumbnail",
    description="""
    Upload a thumbnail image for a hymn book.
- **hymn_book_id**: The ID of the hymn book.
- **thumbnail**: The image file (JPEG or PNG).
- Requires authentication and `update_hymn_book` permission.
    """,
    response_description="Confirmation of successful upload",
)
async def upload_hymn_book_thumbnail(
    hymn_book_id: str,
    thumbnail: UploadFile = File(..., description="Thumbnail image (JPEG or PNG)"),
    db: AsyncSession = Depends(get_db),
    current_user: UserOut = Depends(check_permission("update_hymn_book")),
):
    updated_book = await update_hymn_book_thumbnail(db, hymn_book_id, thumbnail, current_user.id)
    if not updated_book:
        raise HTTPException(status_code=404, detail="Hymn book not found")
    return {"detail": "Thumbnail uploaded"}

@router.delete(
    "/hymn_books/{hymn_book_id}",
    summary="Delete a hymn book",
    description="""
    Delete a hymn book and its thumbnail file.
- **hymn_book_id**: The ID of the hymn book.
- Requires authentication and `delete_hymn_book` permission.
    """,
    response_description="Confirmation of deletion",
)
async def delete_hymn_book_endpoint(
    hymn_book_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserOut = Depends(check_permission("delete_hymn_book")),
):
    deleted_book = await delete_hymn_book(db, hymn_book_id, current_user.id)
    if not deleted_book:
        raise HTTPException(status_code=404, detail="Hymn book not found")
    return {"detail": "Hymn book deleted"}

@router.post(
    "/hymns",
    response_model=HymnOut,
    summary="Create a new hymn",
    description="""
    Create a new hymn in a hymn book.
- **hymn**: Hymn details (title, number, content with verses as list of {verse_tag, verse_name, verse_content}, optional chorus, optional variant_key).
- Requires authentication and `create_hymn` permission.
- Validates content: at least one verse; chorus optional.
    """,
    response_description="The created hymn",
)
async def create_hymn_endpoint(
    hymn: HymnCreate = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: UserOut = Depends(check_permission("create_hymn")),
):
    return await create_hymn(db, hymn, current_user.id)

@router.get(
    "/hymns/{hymn_id}",
    response_model=HymnOut,
    summary="Get a hymn by ID",
    description="""
    Retrieve a specific hymn.
- **hymn_id**: The ID of the hymn.
- Public endpoint (no authentication required).
    """,
    response_description="The hymn object",
)
async def read_hymn(
    hymn_id: str,
    db: AsyncSession = Depends(get_db),
):
    hymn = await get_hymn(db, hymn_id)
    if not hymn:
        raise HTTPException(status_code=404, detail="Hymn not found")
    return hymn

@router.put(
    "/hymns/{hymn_id}",
    response_model=HymnOut,
    summary="Update a hymn",
    description="""
    Update an existing hymn.
- **hymn_id**: The ID of the hymn.
- **hymn**: Updated hymn details (verses as list of {verse_tag, verse_name, verse_content}, optional chorus, optional variant_key).
- Requires authentication and `update_hymn` permission.
- Validates content: at least one verse; chorus optional.
    """,
    response_description="The updated hymn",
)
async def update_hymn_endpoint(
    hymn_id: str,
    hymn: HymnUpdate = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: UserOut = Depends(check_permission("update_hymn")),
):
    updated_hymn = await update_hymn(db, hymn_id, hymn, current_user.id)
    if not updated_hymn:
        raise HTTPException(status_code=404, detail="Hymn not found")
    return updated_hymn

@router.delete(
    "/hymns/{hymn_id}",
    summary="Delete a hymn",
    description="""
    Delete a hymn from a hymn book.
- **hymn_id**: The ID of the hymn.
- Requires authentication and `delete_hymn` permission.
    """,
    response_description="Confirmation of deletion",
)
async def delete_hymn_endpoint(
    hymn_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserOut = Depends(check_permission("delete_hymn")),
):
    deleted_hymn = await delete_hymn(db, hymn_id, current_user.id)
    if not deleted_hymn:
        raise HTTPException(status_code=404, detail="Hymn not found")
    return {"detail": "Hymn deleted"}

@router.get(
    "/hymn_books/{hymn_book_id}/hymns",
    response_model=List[HymnSearchResult],
    summary="Get hymns by hymn book ID",
    description="Retrieve all hymns belonging to a specific hymn book.",
    response_description="List of hymns in the hymn book",
)
async def get_hymns_by_hymn_book(
    hymn_book_id: str,
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    hymns = await get_hymns_by_hymn_book_id(db, hymn_book_id, skip, limit)
    return hymns


@router.get(
    "/search",
    response_model=List[HymnSearchResult],
    summary="Search hymns by filters",
    description="Search hymns using optional filters: title (partial match), number, hymn_book_id.",
    response_description="List of matching hymns",
)
async def search_hymns_filtered(
    filters: HymnFilterParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    return await search_hymns_by_filters(
        db,
        title=filters.title,
        number=filters.number,
        hymn_book_id=filters.hymn_book_id,
        skip=filters.skip,
        limit=filters.limit,
    )

@router.get(
    "/hymns/{hymn_id}/variants",
    response_model=List[HymnVariantResult],
    summary="Get hymn variants",
    description="""
    Get all variants/versions of a hymn from other books.
- **hymn_id**: The ID of the base hymn.
- Matches by `variant_key` or title similarity.
- Public endpoint.
    """,
    response_description="List of variant hymns",
)
async def get_hymn_variants_endpoint(
    hymn_id: str,
    db: AsyncSession = Depends(get_db),
):
    return await get_hymn_variants(db, hymn_id)