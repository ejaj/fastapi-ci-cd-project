from fastapi import APIRouter, status, HTTPException

router = APIRouter(prefix="/status", tags=["Response Status Codes"])

FAKE_DB = {"1": "Pen", "2": "Book"}


@router.post("/items", status_code=status.HTTP_201_CREATED)
async def create_item(name: str):
    return {"message": f"Item '{name}' created"}


@router.get("/items/{item_id}", status_code=status.HTTP_200_OK)
async def get_item(item_id: str):
    if item_id not in FAKE_DB:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return {"item": FAKE_DB[item_id]}


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: str):
    if item_id not in FAKE_DB:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    del FAKE_DB[item_id]
    return  # No content
