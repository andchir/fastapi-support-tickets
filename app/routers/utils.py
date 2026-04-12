import uuid
from fastapi import APIRouter

router = APIRouter()


@router.post("/uuid")
async def generate_uuid():
    return {"uuid": str(uuid.uuid4())}
