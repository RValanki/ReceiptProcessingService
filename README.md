## Welcome to Receipt Processing Service!
**Initial Setup**

Add `.env` file to `azure` directory and add these keys with your values:
```commandline
AZURE_FORM_RECOGNIZER_KEY=  
AZURE_FORM_RECOGNIZER_ENDPOINT= 
```
**Coles E-Receipt Script**

To run coles E-Receipt Script run:
```commandline
cd "$(git rev-parse --show-toplevel)"
python -m src.azure.coles     
```

**Woolworths E-Receipt Script**

To run coles E-Receipt Script run:
```commandline
cd "$(git rev-parse --show-toplevel)"
python -m src.azure.woolworths     
```