from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.schemas import Page
from app.modules.auth.dependencies import admin_only
from app.modules.patterns import service
from app.modules.patterns.schemas import FileIn, FileOut, PatternIn, PatternOut

router = APIRouter(prefix="/admin/patterns", tags=["admin: patterns"])


@router.get("", response_model=Page[PatternOut])
def list_patterns(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    q: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(admin_only),
):
    return service.list_patterns(db, limit, offset, q)


@router.post("", response_model=PatternOut, status_code=status.HTTP_201_CREATED)
def create_pattern(data: PatternIn, db: Session = Depends(get_db), user=Depends(admin_only)):
    return service.create_pattern(db, user, data)


@router.get("/{pattern_id}", response_model=PatternOut)
def get_pattern(pattern_id: int, db: Session = Depends(get_db), user=Depends(admin_only)):
    return service.get_pattern(db, pattern_id)


@router.put("/{pattern_id}", response_model=PatternOut)
def update_pattern(
    pattern_id: int, data: PatternIn, db: Session = Depends(get_db), user=Depends(admin_only)
):
    return service.update_pattern(db, user, pattern_id, data)


@router.delete("/{pattern_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pattern(pattern_id: int, db: Session = Depends(get_db), user=Depends(admin_only)):
    service.delete_pattern(db, user, pattern_id)


@router.post("/{pattern_id}/files", response_model=FileOut, status_code=status.HTTP_201_CREATED)
def add_file(
    pattern_id: int, data: FileIn, db: Session = Depends(get_db), user=Depends(admin_only)
):
    return service.add_file(db, user, pattern_id, data)


@router.put("/{pattern_id}/files/{file_id}", response_model=FileOut)
def update_file(
    pattern_id: int,
    file_id: int,
    data: FileIn,
    db: Session = Depends(get_db),
    user=Depends(admin_only),
):
    return service.update_file(db, user, pattern_id, file_id, data)


@router.delete("/{pattern_id}/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
    pattern_id: int, file_id: int, db: Session = Depends(get_db), user=Depends(admin_only)
):
    service.delete_file(db, user, pattern_id, file_id)