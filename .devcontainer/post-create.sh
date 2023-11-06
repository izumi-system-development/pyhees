#!/usr/bin/env sh

git config --global core.autocrlf false

# pip の更新
pip install --user -U pip

# numpy, pandas などは Pyhees 使用バージョンが自動的に追加されるため不要
pip install --user -r requirements.txt
