import os
import dataclasses
import json
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from src.azure.woolworths import parse_receipt_items  # your existing parsing function

app = FastAPI()


@app.post("/parse-receipt/")
async def parse_receipt(file: UploadFile = File(...)):
    temp_file_path = None
    try:
        # Save the uploaded file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        # Parse the receipt using your existing function
        receipt = parse_receipt_items(temp_file_path)

        # Convert dataclass to dict for JSON serialization
        receipt_dict = dataclasses.asdict(receipt)

        return JSONResponse(content=receipt_dict)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Clean up the temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)


if __name__ == "__main__":
    import uvicorn
    # Run the app with autoreload for dev convenience
    uvicorn.run("src.app:app", host="0.0.0.0", port=8000, reload=True)
