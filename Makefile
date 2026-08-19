.PHONY: smoke test install

# Offline smoke: evaluates the sentiment scorer on a bundled toy tweet set and
# exercises the Flask predict endpoint in-process. No network, no Twitter API.
smoke:
	python scripts/smoke.py

test:
	python -m pytest -q

install:
	pip install -r requirements.txt
