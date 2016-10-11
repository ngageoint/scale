#!/usr/bin/env sh

if [ -n "$1" ]
then
    echo "Overriding default NPM registry configuration with $1..."
    echo "\nregistry = $1\n" >> ~/.npmrc
else
    echo "Default NPM configuration being used."
fi
