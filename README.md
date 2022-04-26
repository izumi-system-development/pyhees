# 自立循環型住宅プロジェクト 検証プラットフォーム 計算プログラム

本プログラムは、自立循環型住宅プロジェクト 検証プラットフォームの計算プログラムです。
[エネルギー消費性能の算定方法に基づく計算ファイル](https://github.com/BRI-EES-House/pyhees)を元に改変を加えて作成しています。

## 実行環境

* Python 3.8.5 以上

## 実行前の準備

```
cd <ソースコードのフォルダ>
pip install -r requirements.txt
```

## 実行方法

気象データを指定しない場合

```
python calc-experiment/main.py < input.json > result.json
```

気象データを指定する場合

```
python calc-experiment/main.py climate.csv outdoor.csv < input.json > result.json
```

## ソースコードの構成

* `calc-experiment/`
    * `main.py` メインプログラム。こちらを呼び出します。
    * `crac_calc_200713_mitaka.py` 旧プログラム。参考のため残しています。
    * `input-sample.json` 入力JSONのサンプル。全てデフォルトの入力値です。
* `jjj-experiment/` 検証プラットフォーム独自のプログラム。
    * `input.py` 検証プラットフォーム用入力JSONを読み込むモジュールです。
    * `calc.py` 検証プラットフォーム独自の計算モジュールです。
    * `constants.py` 計算時定数の変更に関するプログラムです。
* `pyhees/` [エネルギー消費性能の算定方法に基づく計算ファイル](https://github.com/BRI-EES-House/pyhees)に一部だけ改変を加えたものです。
