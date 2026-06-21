from fastapi import APIRouter, HTTPException, status, Body
from typing import List, Dict, Any
from app.services.storage_manager import storage

router = APIRouter(prefix="/tables", tags=["Tables"])

@router.get("/{table_name}", response_model=List[Dict[str, Any]])
async def retrieve_table(table_name: str):
    try:
        return storage.get_table(table_name)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{table_name}/update", status_code=status.HTTP_200_OK, summary="Overwrite Entire Table", description="To update, copy the JSON from the GET endpoint, paste it here, and modify your values.")
async def update_record(table_name: str, data: List[Dict[str, Any]] = Body(..., description="Paste the entire JSON array from the GET request here, containing your edits.")):
    try:
        storage.update_record(table_name, data)
        updated_data = storage.get_table(table_name)
        return {"message": "Table updated successfully", "data": updated_data}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

