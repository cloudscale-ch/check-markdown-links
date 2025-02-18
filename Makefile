.PHONY: venv
venv:
	python3.12 -m venv --clear venv
	venv/bin/pip install --editable '.[dev]'

.PHONY: mypy
mypy:
	venv/bin/mypy

.PHONY: pytest
pytest:
	venv/bin/pytest
