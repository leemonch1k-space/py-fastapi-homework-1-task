import math
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, MovieModel
from schemas import MovieDetailResponseSchema, MovieListResponseSchema


router = APIRouter()

PAGE_BASE_URL = "/theater/movies/"

@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
        db: Annotated[AsyncSession,
        Depends(get_db)],
        page: int,
        per_page: int
):
    # Handling query exceptions
    if page <= 0 or per_page <= 0:
        invalid_query = None

        if page <= 0 < per_page:
            invalid_query = "page"
        elif per_page <= 0 < page:
            invalid_query = "per_page"
        else:
            invalid_query = ["page", "per_page"]

        raise HTTPException(
            status_code=422,
            detail=[
                {
                    "loc": ["query", invalid_query],
                    "msg": "ensure this value is greater than or equal to 1",
                    "type": "value_error.number.not_ge"
                }
            ]
        )

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