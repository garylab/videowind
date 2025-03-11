

# Usage
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

To start api server:
```bash
python src/main.py
```

To start Streamlit app:
```bash
streamlit run ./streamlit/Main.py --browser.serverAddress="0.0.0.0" --server.enableCORS=True --browser.gatherUsageStats=False
```