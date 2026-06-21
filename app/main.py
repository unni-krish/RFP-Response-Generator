from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.routes import health, tables, files
from app.services.storage_manager import storage
from app.utils.logger import logger

app = FastAPI(
    title="Resource Storage Service",
    description="""
### How to Edit and Update Tables in Swagger
1. Open the **GET /tables/{table_name}** endpoint below.
2. Enter your table name (e.g., `rate_card` or `delivery_methodology`) and click **Execute**.
3. **Copy the entire JSON array** from the Response body.
4. Scroll down to the **PUT /tables/{table_name}/update** endpoint.
5. **Paste the copied JSON array** into the Request body box.
6. Modify the specific values you want to update inside the text box (e.g., changing `"hourly_rate_usd": 150` to `160`).
7. Click **Execute** to save the updated table!""",
    version="1.0.0"
)

# Include routers
app.include_router(health.router)
app.include_router(tables.router)
app.include_router(files.router)
@app.get("/resources", tags=["Global"])
async def retrieve_entire_storage():
    """Retrieve complete JSON structure."""
    try:
        return storage.get_all()
    except Exception as e:
        logger.error(f"Error retrieving complete storage: {str(e)}")
        return JSONResponse(status_code=500, content={"detail": str(e)})

@app.on_event("startup")
async def startup_event():
    logger.info("Resource Storage Service started.")
