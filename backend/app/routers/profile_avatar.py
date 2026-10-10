"""Owned profile avatars. Re-encode uploads to remove metadata and active content."""
import base64,io,warnings
from typing import Literal
from fastapi import APIRouter,UploadFile,File,HTTPException
from pydantic import BaseModel,ConfigDict
from PIL import Image,ImageOps,UnidentifiedImageError
from ..db import col
from ..security import StudentId,iso_now

router=APIRouter(prefix='/profile',tags=['profile-avatar'])
PRESETS={f'{style}-{index}' for style in ('student','coder','ai','hero','minimal','initials','scholar','explorer') for index in (1,2)}
MAX_BYTES=5*1024*1024
class AvatarChoice(BaseModel):
    model_config=ConfigDict(extra='forbid')
    presetId:str

async def save(student_id,avatar):
    result=await col('profiles').update_one({'studentId':student_id},{'$set':{'avatar':avatar,'updatedAt':iso_now()}})
    if not result.matched_count:raise HTTPException(404,'Profile not found.')
    return {'avatar':avatar}

@router.put('/avatar')
async def choose(payload:AvatarChoice,student_id:str=StudentId):
    if payload.presetId not in PRESETS:raise HTTPException(422,'Choose an available avatar.')
    return await save(student_id,{'kind':'preset','presetId':payload.presetId})

@router.delete('/avatar')
async def reset(student_id:str=StudentId):return await save(student_id,None)

@router.post('/photo')
async def upload(file:UploadFile=File(...),student_id:str=StudentId):
    if file.content_type not in {'image/jpeg','image/png','image/webp'}:raise HTTPException(415,'Use JPG, PNG or WebP.')
    raw=await file.read(MAX_BYTES+1)
    if len(raw)>MAX_BYTES:raise HTTPException(413,'Photo must be 5 MB or smaller.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error',Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as source:
                if source.format not in {'JPEG','PNG','WEBP'}:raise ValueError('Invalid format')
                if source.width*source.height>16_000_000:raise ValueError('Photo exceeds 16 megapixels')
                source.load()
                oriented=ImageOps.exif_transpose(source).convert('RGBA')
                square=ImageOps.fit(oriented,(384,384),method=Image.Resampling.LANCZOS)
                background=Image.new('RGB',square.size,'#f1f5f9');background.paste(square,mask=square.getchannel('A'))
                output=io.BytesIO();background.save(output,'WEBP',quality=88)
    except (UnidentifiedImageError,OSError,ValueError,Image.DecompressionBombError,Image.DecompressionBombWarning):
        raise HTTPException(422,'Photo could not be decoded. Use a valid JPG, PNG or WebP up to 16 megapixels.')
    avatar={'kind':'photo','dataUrl':'data:image/webp;base64,'+base64.b64encode(output.getvalue()).decode('ascii')}
    return await save(student_id,avatar)
