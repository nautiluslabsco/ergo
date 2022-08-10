#!/usr/bin/env bash

source ./scripts/shared.sh

mod=${1:-$(diffed_files)}

exit_code=0

printf "\e[1mFormatting code (autopep) ...\e[0m\n"
autopep8 --aggressive --diff --exit-code --recursive $mod
if [ $? -ne 0 ]; then exit_code=1; fi

printf "\e[1mFormatting code (black) ...\e[0m\n"
black -S --line-length 512 $mod --check --diff
if [ $? -ne 0 ]; then exit_code=1; fi

printf "\e[1mSorting imports (isort) ...\e[0m\n"
isort $mod -c
if [ $? -ne 0 ]; then exit_code=1; fi

printf "\e[1mLinting (pylint) ...\e[0m\n"
pylint -d too-few-public-methods -d missing-docstring -d unused-argument -d unused-variable -d line-too-long $mod
if [ $? -ne 0 ]; then exit_code=1; fi

printf "\e[1mType Checking (mypy) ...\e[0m\n"
mypy --strict $mod
if [ $? -ne 0 ]; then exit_code=1; fi

printf "\e[1mComplexity check ...\e[0m\n"
xenon --max-absolute A --max-modules A --max-average A $mod
if [ $? -ne 0 ]; then exit_code=1; fi
xenon --max-absolute B --max-modules A --max-average A $mod
if [ $? -ne 0 ]; then exit_code=1; fi

printf "\e[32mSuccess.\e[0m\n"

exit $exit_code
