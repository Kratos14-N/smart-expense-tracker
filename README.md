# Smart Expense Tracker

A local Streamlit app for recording expenses, setting a monthly spending limit, reviewing category totals, and comparing monthly spending.

## Run locally

```powershell
python -m pip install -r requirements.txt
python -m streamlit run finance.py
```

The app creates `expenses.db` beside `finance.py` when it runs. That local database is excluded from Git so personal expense records are not published.
