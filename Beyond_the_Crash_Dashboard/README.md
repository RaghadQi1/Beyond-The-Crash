# BEYOND THE CRASH — Six Investigation Cases

Notebook reference: `Beyond_the_Crash_Six_Cases_Final-2.ipynb`. The bundled `CAROL_Aviation_EDA.csv` contains **6,701 records**, matching the notebook’s documented main analysis population. Another supplied file named `CAROL_Aviation_EDA(1).csv` contained only **1,626 records (2023–2026)** and was not substituted for the notebook’s 6,701-record population. If using that file intentionally, expect different outputs.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The CSV is bundled next to `app.py`; no upload is needed. For Streamlit Community Cloud deploy the contents of this folder to a GitHub repository root, choose `app.py`, and keep `requirements.txt` and the CSV in that same folder.

The dashboard reproduces *definitions and six analytical questions* from the notebook; live filter states recompute figures and can differ from the unfiltered notebook findings.
