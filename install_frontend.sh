#!/usr/bin/env bash

VERSION=0

# remove existing ones
rm -rf server/static server/templates

if [ $VERSION -eq 0 ]
then
   cp -r frontend/v0/static server/static
   cp -r frontend/v0/templates server/templates
else
   mkdir -p server/static
   mkdir -p server/templates
   cp frontend/v1/index.html server/templates
   # todo: need to have build folder to put bundle.js
   cp frontend/v1/bundle.js server/static
fi
