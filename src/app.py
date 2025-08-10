import os
import dataclasses
import json
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from src.azure.woolworths import parse_receipt_items as parse_woolworths_receipt
from src.azure.coles import parse_receipt_items as parse_coles_receipt

app = FastAPI()


async def handle_upload(file: UploadFile, parser_func):
    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        receipt = parser_func(temp_file_path)
        receipt_dict = dataclasses.asdict(receipt)
        return JSONResponse(content=receipt_dict)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@app.post("/parse-receipt/woolworths/")
async def parse_woolworths(file: UploadFile = File(...)):
    return await handle_upload(file, parse_woolworths_receipt)


@app.post("/parse-receipt/coles/")
async def parse_coles(file: UploadFile = File(...)):
    return await handle_upload(file, parse_coles_receipt)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.app:app", host="0.0.0.0", port=8000, reload=True)
