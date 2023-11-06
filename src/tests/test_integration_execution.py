import pytest
import json
import copy

from jjjexperiment.main import calc
from jjjexperiment.logger import LimitedLoggerAdapter as _logger

#from os.path import join, dirname
from os import pardir, path
import sys

sys.path.append(path.dirname(__file__))
print(sys.path)
from .test_utils.utils import *

class Test既存計算維持_デフォルト入力時:

    # WARNING: 現状プラットフォームのデフォルト入力が 潜熱バグFix=OFF となっている
    # 正しい結果が必要なら fix_latent_load = 2 に上書きする
    # print( join(pardir(dirname(__file__)), INPUT_SAMPLE_TYPE1_PATH) )
    # print(INPUT_SAMPLE_TYPE1_PATH)
    # print(pardir(path.dirname(__file__)))
    # print(INPUT_SAMPLE_TYPE1_PATH)
    _inputs1: dict = json.load(open(path.join(path.dirname(__file__), INPUT_SAMPLE_TYPE1_PATH), 'r'))
    _inputs2: dict = json.load(open(path.join(path.dirname(__file__), INPUT_SAMPLE_TYPE2_PATH), 'r'))
    _inputs3: dict = json.load(open(path.join(path.dirname(__file__), INPUT_SAMPLE_TYPE3_PATH), 'r'))
    _inputs4: dict = json.load(open(path.join(path.dirname(__file__), INPUT_SAMPLE_TYPE4_PATH), 'r'))

    def fix_latent_bug(self, inputs: dict) -> dict:
        """ 潜熱バグ修正時の計算結果を確認したい時に使用する
        """
        inputs.update({"fix_latent_load": "2"})
        # NOTE: もしも calc に通さないなら追加で set_constants() が必要
        return inputs

    def test_インプットデータ_前提確認(self, expected_inputs):
        """ テストコードが想定しているインプットデータかどうか確認
        """
        result = calc(self._inputs1, test_mode=True)

        assert result['TInput'].q_rtd_C == expected_inputs.q_rtd_C
        assert result['TInput'].q_rtd_H == expected_inputs.q_rtd_H
        assert result['TInput'].q_max_C == expected_inputs.q_max_C
        assert result['TInput'].q_max_H == expected_inputs.q_max_H
        assert result['TInput'].e_rtd_C == expected_inputs.e_rtd_C
        assert result['TInput'].e_rtd_H == expected_inputs.e_rtd_H

    def test_計算実行_バリデーションしない(self):
        """
        """
        _logger.init_logger()
        inputs = self.fix_latent_bug(self._inputs1)

        fixtures = {
                "U_A": 0.60,  # 0.86
                "H_A": {"VAV": 2},
                "C_A": {"VAV": 2},
            }
        inputs = deep_update(copy.deepcopy(inputs), fixtures)

        result = calc(inputs, test_mode=True)

    def test_計算結果一致_方式1(self, expected_result_type1):
        """ ipynbのサンプル入力で計算結果が意図しない変化がないことを確認
        """
        _logger.init_logger()
        result = calc(self._inputs1, test_mode=True)

        assert result['TValue'].E_C == expected_result_type1.E_C
        assert result['TValue'].E_H == expected_result_type1.E_H

    def test_計算結果一致_方式2(self, expected_result_type2):
        """ ipynbのサンプル入力で計算結果が意図しない変化がないことを確認
        """
        _logger.init_logger()
        result = calc(self._inputs2, test_mode=True)

        assert result['TValue'].E_C == expected_result_type2.E_C
        assert result['TValue'].E_H == expected_result_type2.E_H

    def test_計算結果一致_方式3(self, expected_result_type1, expected_result_type2):
        """ 方式3 最後まで実行できること、結果がちゃんと変わることだけ確認
        """
        _logger.init_logger()
        result = calc(self._inputs3, test_mode=True)

        assert result['TValue'].E_C != expected_result_type1.E_C
        assert result['TValue'].E_H != expected_result_type1.E_H

        assert result['TValue'].E_C != expected_result_type2.E_C
        assert result['TValue'].E_H != expected_result_type2.E_H

    def test_計算結果一致_方式4(self, expected_result_type1, expected_result_type2):
        """ 方式4 最後まで実行できること、結果がちゃんと変わることだけ確認
        """
        _logger.init_logger()
        result = calc(self._inputs4, test_mode=True)

        assert result['TValue'].E_C != expected_result_type1.E_C
        assert result['TValue'].E_H != expected_result_type1.E_H

        assert result['TValue'].E_C != expected_result_type2.E_C
        assert result['TValue'].E_H != expected_result_type2.E_H
