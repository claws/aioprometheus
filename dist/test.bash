#!/usr/bin/env bash

if [ -z "$1" ]; then
  echo "usage: $0 aioprometheus-YY.MM.MICRO.tar.gz"
  exit
fi

RELEASE_ARCHIVE="$1"
RELEASE_DIR=`echo $RELEASE_ARCHIVE | sed -e "s/\.tar\.gz//g"`

echo "Release archive: $RELEASE_ARCHIVE"
echo "Release directory: $RELEASE_DIR"

echo "Removing any old artefacts"
rm -rf $RELEASE_DIR
rm -rf test_venv

echo "Creating test virtual environment"
python -m venv test_venv

echo "Entering test virtual environment"
source test_venv/bin/activate

echo "Upgrading pip"
pip install pip --upgrade

echo "Installing $RELEASE_ARCHIVE"
tar xf $RELEASE_ARCHIVE
cd $RELEASE_DIR
pip install .

echo "Running tests"
make test
cd ..

echo "Exiting test virtual environment"
deactivate
