from enum import Enum

# NOTE: プラットフォーム上の選択肢と一致させます

class 熱源機出口の空気温度(Enum):
    従来の計算 = 1
    式を変更 = 2

class VAVありなしの吹出風量(Enum):
    数式を統一しない = 1
    数式を統一する = 2

class Vサプライの上限キャップ(Enum):
    外さない = 1
    全体でキャップ = 2
    ピンポイントでキャップ = 3

class 過剰熱量繰越計算(Enum):
    行わない = 1
    行う = 2
