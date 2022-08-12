#!/usr/bin/env bash

source ./scripts/shared.sh

mod=${1:-$(diffed_files)}

printf "\e[1mFormatting code (autopep) ...\e[0m\n"
autopep8 --in-place --aggressive --recursive $mod
if [ $? -ne 0 ]; then { printf "\e[31mFailed, aborting.\e[0m\n" ; exit 1; } fi

printf "\e[1mFormatting code (black) ...\e[0m\n"
black -S --line-length 512 $mod
if [ $? -ne 0 ]; then { printf "\e[31mFailed, aborting.\e[0m\n" ; exit 1; } fi

printf "\e[1mSorting imports (isort) ...\e[0m\n"
isort $mod
if [ $? -ne 0 ]; then { printf "\e[31mFailed, aborting.\e[0m\n" ; exit 1; } fi

printf "\e[32mSuccess.\e[0m\n"
