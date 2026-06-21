# pyrefly: ignore [missing-import]
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import tempfile
import os
import shutil
import logging
import json
from app.orchestrator import run_pipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

app = FastAPI(
    title="Architecture Service",
    description="Architecture deck workflow microservice",
    version="1.0.0",
    docs_url="/api/v1/architecture/docs",
    openapi_url="/api/v1/architecture/openapi.json"
)

@app.get("/api/v1/architecture/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "Architecture Service"}

@app.post("/api/v1/architecture/generate")
async def generate_architecture_deck(
    file: UploadFile = File(...),
    state_payload: str = Form("{}")
):
    """
    Generate an Architecture Deck (PPTX) from an uploaded RFP PDF.
    """
    if not file.filename.endswith('.pdf') and not file.filename.endswith('.docx'):
        raise HTTPException(status_code=400, detail="Only PDF or DOCX files are supported")
        
    try:
        # Create a temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            input_dir = os.path.join(temp_dir, "input")
            output_dir = os.path.join(temp_dir, "output")
            os.makedirs(input_dir, exist_ok=True)
            os.makedirs(output_dir, exist_ok=True)
            
            # Save uploaded file
            file_path = os.path.join(input_dir, file.filename)
            with open(file_path, "wb") as f:
                f.write(await file.read())
                
            logger.info(f"Processing uploaded file: {file.filename}")
            
            # Parse the state payload
            try:
                provided_state = json.loads(state_payload)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="state_payload must be valid JSON")
            
            # Run the pipeline — always fresh (testing_mode=False) so the
            # uploaded file is processed, not a cached previous result.
            pptx_path, final_state = run_pipeline(input_dir, output_dir, testing_mode=False, provided_state=provided_state)
            
            if not pptx_path or not os.path.exists(pptx_path):
                raise HTTPException(status_code=500, detail="Failed to generate the PPTX file.")
                
            # Create a persistent copy of the files in the global output directory
            # so that they can be retrieved later
            from app.utils.config import load_config
            config_data = load_config()
            global_output_folder = config_data.get("paths", {}).get("output_folder", "output")
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            global_output_dir = os.path.join(base_dir, global_output_folder)
            os.makedirs(global_output_dir, exist_ok=True)
            
            final_output_path = os.path.join(global_output_dir, "Architecture_Proposal.pptx")
            try:
                shutil.copyfile(pptx_path, final_output_path)
            except Exception as e:
                logger.error(f"Failed to copy PPTX to global output: {e}")
            
            # Copy diagram image if exists
            diagram_tmp_path = os.path.join(output_dir, "architecture_diagram.png")
            if os.path.exists(diagram_tmp_path):
                try:
                    shutil.copyfile(diagram_tmp_path, os.path.join(global_output_dir, "architecture_diagram.png"))
                except Exception as e:
                    pass
                
            # Copy the final_state.json file to the global output directory
            state_tmp_path = os.path.join(output_dir, "final_state.json")
            if os.path.exists(state_tmp_path):
                try:
                    shutil.copyfile(state_tmp_path, os.path.join(global_output_dir, "final_state.json"))
                except Exception as e:
                    pass
            
            return JSONResponse(content=final_state)
            
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/v1/architecture/download")
async def download_architecture_deck():
    """
    Download the most recently generated Architecture Deck.
    """
    try:
        from app.utils.config import load_config
        config = load_config()
        output_folder = config.get("paths", {}).get("output_folder", "output")
        
        # Resolve base directory (project root)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        pptx_path = os.path.join(base_dir, output_folder, "Architecture_Proposal.pptx")
        
        if not os.path.exists(pptx_path):
            raise HTTPException(status_code=404, detail="Architecture deck not found. Please generate one first.")
            
        return FileResponse(
            path=pptx_path,
            filename="Architecture_Deck.pptx",
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/v1/architecture/diagram/base64")
async def get_diagram_base64():
    """
    Get the most recently generated architecture diagram as a base64 encoded string.
    """
    try:
        import base64
        from app.utils.config import load_config
        config_data = load_config()
        output_folder = config_data.get("paths", {}).get("output_folder", "output")
        
        # Resolve base directory (project root)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        diagram_path = os.path.join(base_dir, output_folder, "architecture_diagram.png")
        
        if not os.path.exists(diagram_path):
            raise HTTPException(status_code=404, detail="Diagram not found. Please generate one first.")
            
        with open(diagram_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            
        return JSONResponse(content={"image_base64": encoded_string})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching diagram base64: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
