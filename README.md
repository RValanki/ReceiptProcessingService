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

### How to run scripts
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