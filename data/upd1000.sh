#!/bin/bash

wget https://hugovk.github.io/top-pypi-packages/top-pypi-packages-30-days.min.json
jq -r '.rows[].project' top-pypi-packages-30-days.min.json > top1000.txt
