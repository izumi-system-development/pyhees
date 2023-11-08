#!/usr/bin/env sh

git config --global core.autocrlf false

# pip の更新
pip install --user -U pip

# numpy, pandas などは Pyhees 使用バージョンが自動的に追加されるため不要
pip install --user -r requirements.txt

# 追加する文字列
export_line="export PYTHONPATH=/workspaces/pyhees/src:workspaces/pyhees/tests"

# .bashrc の末尾に追加
echo "$export_line" >> ~/.bashrc

# 現在のシェルで反映
source ~/.bashrc
