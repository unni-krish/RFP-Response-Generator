from fastapi import APIRouter, HTTPException, status, Body
from typing import Any
from app.services.storage_manager import storage

router = APIRouter(prefix="/files", tags=["Files"])


@router.get("/{file_name}", status_code=status.HTTP_200_OK)
async def retrieve_file(file_name: str):
    try:
        return storage.get_file(file_name)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/{file_name}", status_code=status.HTTP_200_OK, summary="Overwrite Entire File", description="To update, copy the content from the GET endpoint, paste it here, and modify.")
async def update_file(file_name: str, content: Any = Body(..., description="Paste the entire file content here.")):
    try:
        storage.update_file(file_name, content)
        updated_content = storage.get_file(file_name)
        return {"message": f"File '{file_name}' updated successfully", "content": updated_content}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

