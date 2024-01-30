echo Loading Versatools...
git pull --all
if not exist .venv python -m venv .venv
call .venv\Scripts\activate
pip install -r requirements.txt
cls
python src\main.py