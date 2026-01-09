ls -al
pwd 

ln -sf /usr/local/bin/python3.11 /usr/bin/python3
python3 --version

PROJECT_VERSION=$(awk '/VERSION = / {print $3}' setup.py)

mkdir -p tests/coverage
chmod +x menlo.sh
./menlo.sh coverage

file tests/coverage/coverage.xml
head -20 tests/coverage/coverage.xml