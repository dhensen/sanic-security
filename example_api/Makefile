
all: venv run


venv:
	pyenv local 3.8
	poetry env use 3.8
	poetry install
	poetry run pip install -e ../sanic-security

run: .regen_keys
	poetry run python3 api.py

.regen_keys:
	openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes -subj '/CN=localhost'
	touch .regen_keys
