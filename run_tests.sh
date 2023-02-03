# run unit tests
python -m unittest discover -v ./test/unit -p 'tests*.py'
# run integration tests
python -m unittest discover -v ./test/integration -p 'tests*.py'