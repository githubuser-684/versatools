echo Loading Versatools...
git pull --all
if not exist .venv python -m venv .venv
call .venv\Scripts\activate
pip install -r requirements.txt
cls
doskey versatools=python src\main.py $*

echo Use 'versatools' to run Versatools.
echo Made by garryybd#0

cmd