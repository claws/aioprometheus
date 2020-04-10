#!/usr/bin/env bash

if [ -z "$1" ]; then
  echo "usage: $0 aioprometheus-YY.MM.MICRO-py3-none-any.whl"
  exit
fi

RELEASE_ARCHIVE="$1"

echo "Release archive: $RELEASE_ARCHIVE"

echo "Removing any old artefacts"
rm -rf test_venv

echo "Creating test virtual environment"
python -m venv test_venv

echo "Entering test virtual environment"
source test_venv/bin/activate

echo "Upgrading pip"
pip install pip --upgrade

echo "Install test dependencies and extras to check integrations"
pip install asynctest requests aiohttp fastapi quart

echo "Installing $RELEASE_ARCHIVE"
pip install $RELEASE_ARCHIVE

echo "Running tests"
cd ..
make test

echo "Exiting test virtual environment"
deactivate
