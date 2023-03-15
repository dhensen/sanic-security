
all: venv run


venv:
	pyenv local 3.8
	poetry env use 3.8
	poetry install
	poetry run pip install -e ../sanic-security

run:
	poetry run python3 api.py
