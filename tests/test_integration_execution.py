import pytest
import json
import copy
from os import path
import sys

sys.path.append(path.dirname(__file__))
print(sys.path)

from src.jjjexperiment.main import calc
from src.jjjexperiment.logger import LimitedLoggerAdapter as _logger

from test_utils.utils import *


class Test既存計算維持_デフォルト入力時:

    _inputs1: dict = json.load(open(INPUT_SAMPLE_TYPE1_PATH, 'r'))

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
