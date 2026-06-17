# Module 4 – Pytest and Sphinx

## Setup
1. Create virtual environment: `python -m venv venv`
2. Activate: `.\venv\Scripts\activate`
3. Install: `pip install -r requirements.txt`
4. Set `DATABASE_URL` (optional, tests mock the database)

## Fresh Install (pip)

1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
2. Activate it:

   Windows:
   ```bash
   .\venv\Scripts\activate
   ```
   Mac/Linux:
   ```bash
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the app:
   ```bash
   python src/app.py
   ```

## Fresh Install (uv)

1. Install uv (if not already):
   ```bash
   pip install uv
   ```
2. Create a virtual environment:
   ```bash
   uv venv
   ```
3. Activate it:

   Windows:
   ```bash
   .\venv\Scripts\activate
   ```
   Mac/Linux:
   ```bash
   source .venv/bin/activate
   ```
4. Install dependencies:
   ```bash
   uv pip sync requirements.txt
   ```
5. Run the app:
   ```bash
   python src/app.py
   ```
