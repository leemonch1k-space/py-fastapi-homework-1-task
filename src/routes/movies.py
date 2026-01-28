import math
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, MovieModel
from schemas import MovieDetailResponseSchema, MovieListResponseSchema


router = APIRouter()

PAGE_BASE_URL = "/theater/movies/"


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
        db: Annotated[AsyncSession, Depends(get_db)],
        page: int = Query(default=1, ge=1),
        per_page: int = Query(default=10, ge=1, le=20)
):
    # Count total movies
    count_query = select(func.count()).select_from(MovieModel)
    total_result = await db.execute(count_query)
    total_items = total_result.scalar() or 0

    # Search current movies
    offset = (page - 1) * per_page
    query = select(MovieModel).offset(offset).limit(per_page)
    result = await db.execute(query)
    movies = result.scalars().all()

    # Handling empty movie list exception
    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = math.ceil(total_items / per_page)

    # Formating urls
    prev_page_url = (
        f"{PAGE_BASE_URL}?page={page - 1}&per_page={per_page}"
        if page > 1 else None
    )
    next_page_url = (
        f"{PAGE_BASE_URL}?page={page + 1}&per_page={per_page}"
        if page < total_pages else None
    )

    return {
        "movies": movies,
        "prev_page": prev_page_url,
        "next_page": next_page_url,
        "total_pages": total_pages,
        "total_items": total_items
    }


@router.get("/movies/{movie_id}/", response_model=MovieDetailResponseSchema)
async def get_movie(movie_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    return movie
