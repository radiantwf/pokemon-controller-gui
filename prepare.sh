#!/bin/bash
python3.12 -m venv venv

source ./venv/bin/activate

pip install --upgrade pip --index-url http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
pip install -r requirements.txt  --index-url http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

auto-py-to-exe