.PHONY: init test_unit test_integration test_all

init:
	@which python3 > /dev/null 2>&1 || (echo "Python 3 is not installed. Please install it." && exit 1)
	@echo "Current directory: $(CURDIR)"
	@[ -d $(CURDIR)/.venv ] || (echo "Creating virtual environment..." && python3 -m venv .venv)
	@echo "Activating virtual environment and installing dependencies..."
	@. .venv/bin/activate && pip install -r requirements.txt

test_unit:
	@echo "Running unit tests..."
	@python -m unittest discover -v ./tests/unit -p 'test*.py'

test_integration:
	@echo "Running integration tests..."
	@python -m unittest discover -v ./tests/integration -p 'tests*.py'

test_all: test_unit test_integration

coverage:
	@pip install coverage
	@echo "Running coverage..."
	@coverage run -m unittest discover -v ./tests/unit -p 'test*.py'
	@coverage report -m
	@coverage xml
	@echo "Coverage report generated in htmlcov/index.html"