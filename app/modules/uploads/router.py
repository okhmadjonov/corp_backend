from fastapi import APIRouter, Depends, File, UploadFile

from app.core.storage import save_upload
from app.modules.auth.dependencies import admin_only

router = APIRouter(prefix="/admin/uploads", tags=["admin: uploads"])


@router.post("")
async def upload_file(file: UploadFile = File(...), user=Depends(admin_only)):
    return await save_upload(file)