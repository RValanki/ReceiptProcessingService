## Welcome to Receipt Processing Service!
### Initial Setup

Add `.env` file to `azure` directory and add these keys with your values:
```commandline
AZURE_FORM_RECOGNIZER_KEY=  
AZURE_FORM_RECOGNIZER_ENDPOINT= 
```

**Install Dependencies**
```commandline
cd "$(git rev-parse --show-toplevel)"
pip install -r requirements.txt
```

### How to run scripts locally
**Coles E-Receipt Script**

To run coles E-Receipt Script run (Receipt Path is optional):
```commandline
cd "$(git rev-parse --show-toplevel)"
python -m src.azure.coles <path_to_receipt_pdf>     
```

**Woolworths E-Receipt Script**

To run coles E-Receipt Script run (Receipt Path is optional):
```commandline
cd "$(git rev-parse --show-toplevel)"
python -m src.azure.woolworths <path_to_receipt_pdf>    
```

### How to run scripts with FastAPI
**Spinup App locally:**
```commandline
uvicorn src.app:app --reload
```

**Test endpoint with this command:**

#### Coles: 
```commandline
curl -X POST "http://127.0.0.1:8000/parse-receipt/coles/" -F "file=@/path/to/your/receipt.pdf"
```

#### Woolworths: 
```commandline
curl -X POST "http://127.0.0.1:8000/parse-receipt/woolworths/" -F "file=@/path/to/your/receipt.pdf"
```

**Test endpoint with Swagger UI:**

http://127.0.0.1:8000/docs
