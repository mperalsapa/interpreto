#!/bin/bash
# exit on error
set -e

# set path to backend
frontend_path="../interpreto-web-back/front-dist"

# build frontend
npm run build
# rm existing front in backend
rm -rf $frontend_path
# create new front in backend
mkdir -p $frontend_path
# copy new front to backend
cp -r dist/* $frontend_path/
# rm dist
rm -rf dist