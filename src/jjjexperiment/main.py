import json
import numpy as np
import pandas as pd
from datetime import datetime

from pyhees.section2_1_b import get_f_prim

from pyhees.section4_1 import calc_heating_load, calc_cooling_load, get_virtual_heating_devices, get_alpha_UT_H_A
from pyhees.section4_1_a import calc_heating_mode

from pyhees.section4_2 import calc_Q_UT_A
from pyhees.section4_2_a import calc_E_E_H_d_t, calc_E_E_C_d_t

# ダクト式セントラル空調機
import pyhees.section4_2_b as dc_spec

# 床下
import pyhees.section3_1 as ld
from pyhees.section3_2 import calc_r_env, get_Q_dash, get_mu_H, get_mu_C

from pyhees.section11_1 import load_climate, get_Theta_ex

import jjjexperiment.input
import jjjexperiment.constants as constants
from jjjexperiment.result import *
from jjjexperiment.logger import LimitedLoggerAdapter as _logger  # デバッグ用ロガー

def version_info() -> str:
    """ 最終編集日をバージョン管理に使用します
    """
    # NOTE: subprocessモジュールによるコミット履歴からの生成は \
    # ipynb 環境では正常に動作しませんでした(returned no-zero exit status 128.)
    return '_20231025'

def calc(input_data : dict, test_mode=False):
    case_name   = input_data['case_name']
    climateFile = input_data['climateFile']
    outdoorFile = input_data['outdoorFile']
    loadFile    = input_data['loadFile']

    with open(case_name + version_info() + '_input.json', 'w') as f:
        json.dump(input_data, f, indent=4)

    # NOTE: set_constants へ移動 { R_g }
    constants.set_constants(input_data)
    type, tatekata, A_A, A_MR, A_OR, region, sol_region = jjjexperiment.input.get_basic(input_data)
    ENV, NV_MR, NV_OR, TS, r_A_ufvnt, underfloor_insulation, underfloor_air_conditioning_air_supply, hs_CAV = jjjexperiment.input.get_env(input_data)
    mode_H, H_A, H_MR, H_OR, H_HS = jjjexperiment.input.get_heating(input_data, region, A_A)
    mode_C, C_A, C_MR, C_OR = jjjexperiment.input.get_cooling(input_data, region, A_A)
    q_rtd_C, q_rtd_H, q_max_C, q_max_H, e_rtd_C, e_rtd_H, dualcompressor_C, dualcompressor_H, input_C_af_C, input_C_af_H = jjjexperiment.input.get_CRAC_spec(input_data)

    print("q_rtd_C, q_rtd_H, q_max_C, q_max_H, e_rtd_C, e_rtd_H")
    print(q_rtd_C, q_rtd_H, q_max_C, q_max_H, e_rtd_C, e_rtd_H)

    _logger.info(f"q_rtd_C [w]: {q_rtd_C}")  # q[W] 送風機の単位[W]と同じ
    _logger.info(f"q_max_C [w]: {q_max_C}")
    _logger.info(f"e_rtd_C [-]: {e_rtd_C}")
    _logger.info(f"q_rtd_H [w]: {q_rtd_H}")
    _logger.info(f"q_max_H [w]: {q_max_H}")
    _logger.info(f"e_rtd_H [-]: {e_rtd_H}")

    # 熱交換型換気の取得
    HEX = jjjexperiment.input.get_heatexchangeventilation(input_data)

    # 太陽熱利用の取得
    SHC = jjjexperiment.input.get_solarheat()

    # 床面積の合計に対する外皮の部位の面積の合計の比
    r_env = calc_r_env(
        method='当該住戸の外皮の部位の面積等を用いて外皮性能を評価する方法',
        A_env=ENV['A_env'],
        A_A=A_A
    )

    # 熱損失係数（換気による熱損失を含まない）
    Q_dash = get_Q_dash(ENV['U_A'], r_env)
    # 熱損失係数
    Q = ld.get_Q(Q_dash)

    # 日射取得係数の取得
    mu_H = get_mu_H(ENV['eta_A_H'], r_env)
    mu_C = get_mu_C(ENV['eta_A_C'], r_env)

    # 実質的な暖房機器の仕様を取得
    spec_MR, spec_OR = get_virtual_heating_devices(region, H_MR, H_OR)

    # 暖房方式及び運転方法の区分
    mode_MR, mode_OR = calc_heating_mode(region=region, H_MR=spec_MR, H_OR=spec_OR)

    # 空調空気を床下を通して給気する場合（YUCACO）の「床下空間全体の面積に対する空気を供給する床下空間の面積の比 (-)」
    YUCACO_r_A_ufvnt = (8.28+16.56+21.53) / (9.52+1.24+3.31+3.31+1.66+8.28+16.56+21.53)


    ##### 暖房負荷の取得（MJ/h）

    L_H_d_t_i: np.ndarray
    """暖房負荷 [MJ/h]"""

    if loadFile == '-':
        L_H_d_t_i, _ = calc_heating_load(region, sol_region, A_A, A_MR, A_OR, Q, mu_H, mu_C, NV_MR, NV_OR, TS, r_A_ufvnt,
                                        HEX, underfloor_insulation, mode_H, mode_C, spec_MR, spec_OR, mode_MR, mode_OR, SHC)
    else:
        load = pd.read_csv(loadFile, nrows=24 * 365)
        L_H_d_t_i = load.iloc[::,:12].T.values

    L_H_d_t: np.ndarray = np.sum(L_H_d_t_i, axis=0)
    """暖房負荷の全区画合計 [MJ/h]"""

    ##### 冷房負荷の取得（MJ/h）
    L_CS_d_t_i: np.ndarray
    """冷房顕熱負荷 [MJ/h]"""
    L_CL_d_t_i: np.ndarray
    """冷房潜熱負荷 [MJ/h]"""

    if loadFile == '-':
        L_CS_d_t_i, L_CL_d_t_i = calc_cooling_load(region, A_A, A_MR, A_OR, Q, mu_H, mu_C, NV_MR, NV_OR, r_A_ufvnt,
                                                underfloor_insulation, mode_C, mode_H, mode_MR, mode_OR, TS, HEX)
    else:
        load = pd.read_csv(loadFile, nrows=24 * 365)
        L_CS_d_t_i = load.iloc[::,12:24].T.values
        L_CL_d_t_i = load.iloc[::,24:].T.values

    L_CS_d_t: np.ndarray = np.sum(L_CS_d_t_i, axis=0)
    """冷房顕熱負荷の全区画合計 [MJ/h]"""
    L_CL_d_t: np.ndarray = np.sum(L_CL_d_t_i, axis=0)
    """冷房潜熱負荷の全区画合計 [MJ/h]"""

    ##### 暖房消費電力の計算（kWh/h）

    def get_V_hs_dsgn_H(H_A: dict, q_rtd_H: float):
        V_fan_rtd_H = H_A['V_fan_rtd_H'] if 'V_fan_rtd_H' in H_A else dc_spec.get_V_fan_rtd_H(q_rtd_H)
        return dc_spec.get_V_fan_dsgn_H(V_fan_rtd_H)

    V_hs_dsgn_H = H_A['V_hs_dsgn_H'] if 'V_hs_dsgn_H' in H_A else get_V_hs_dsgn_H(H_A, q_rtd_H)
    """ 暖房時の送風機の設計風量[m3/h] """
    V_hs_dsgn_C: float = None  # NOTE: 暖房負荷計算時は空
    """ 冷房時の送風機の設計風量[m3/h] """

    Q_UT_H_d_t_i: np.ndarray
    """暖房設備機器等の未処理暖房負荷(MJ/h)"""

    _, Q_UT_H_d_t_i, _, _, Theta_hs_out_d_t, Theta_hs_in_d_t, _, _, V_hs_supply_d_t, V_hs_vent_d_t, C_df_H_d_t \
        = calc_Q_UT_A(A_A, A_MR, A_OR, r_env, mu_H, mu_C,
            H_A['q_hs_rtd_H'], None, V_hs_dsgn_H, V_hs_dsgn_C, Q,
            H_A['VAV'], H_A['general_ventilation'], H_A['duct_insulation'], region, L_H_d_t_i, L_CS_d_t_i, L_CL_d_t_i)
    climate = load_climate(region)
    Theta_ex_d_t = get_Theta_ex(climate)

    _logger.NDdebug("Q_UT_H_d_t_i", Q_UT_H_d_t_i[0])

    E_E_H_d_t: np.ndarray
    """日付dの時刻tにおける1時間当たりの暖房時の消費電力量(kWh/h)"""

    E_E_H_d_t = calc_E_E_H_d_t(
        Theta_hs_out_d_t = Theta_hs_out_d_t,
        Theta_hs_in_d_t = Theta_hs_in_d_t,
        V_hs_supply_d_t = V_hs_supply_d_t,
        V_hs_vent_d_t = V_hs_vent_d_t,
        C_df_H_d_t = C_df_H_d_t,
        q_hs_rtd_H = H_A['q_hs_rtd_H'],
        V_hs_dsgn_H = V_hs_dsgn_H,
        P_hs_mid_H = H_A['P_hs_mid_H'],
        P_hs_rtd_H = H_A['P_hs_rtd_H'],
        P_fan_rtd_H = H_A['P_fan_rtd_H'],
        P_fan_mid_H = H_A['P_fan_mid_H'],
        q_hs_min_H = H_A['q_hs_min_H'],
        q_hs_mid_H = H_A['q_hs_mid_H'],
        V_fan_rtd_H = H_A['V_fan_rtd_H'],
        V_fan_mid_H = H_A['V_fan_mid_H'],
        EquipmentSpec = H_A['EquipmentSpec'],
        region = region)


    alpha_UT_H_A: float = get_alpha_UT_H_A(region)
    """未処理暖房負荷を未処理暖房負荷の設計一次エネルギー消費量相当値に換算するための係数"""
    Q_UT_H_A_d_t: np.ndarray = np.sum(Q_UT_H_d_t_i, axis=0)
    """未処理暖房負荷の全機器合計(MJ/h)"""
    E_UT_H_d_t: np.ndarray = Q_UT_H_A_d_t * alpha_UT_H_A
    """未処理暖房負荷の設計一次エネルギー消費量相当値(MJ/h)"""

    df_output2 = pd.DataFrame(index = pd.date_range(datetime(2023,1,1,1,0,0), datetime(2024,1,1,0,0,0), freq='h'))
    df_output2['Q_UT_H_d_A_t [MJ/h']        = Q_UT_H_A_d_t
    df_output2['Theta_hs_H_out_d_t [℃]']    = Theta_hs_out_d_t
    df_output2['Theta_hs_H_in_d_t [℃]']     = Theta_hs_in_d_t
    df_output2['Theta_ex_d_t [℃]']          = Theta_ex_d_t
    df_output2['V_hs_supply_H_d_t [m3/h]']  = V_hs_supply_d_t
    df_output2['V_hs_vent_H_d_t [m3/h]']    = V_hs_vent_d_t
    df_output2['C_df_H_d_t [-]']            = C_df_H_d_t

    ##### 冷房消費電力の計算（kWh/h）

    def get_V_hs_dsgn_C(C_A: dict, q_rtd_C: float):
        V_fan_rtd_C = C_A['V_fan_rtd_C'] if 'V_fan_rtd_C' in C_A else dc_spec.get_V_fan_rtd_C(q_rtd_C)
        return dc_spec.get_V_fan_dsgn_C(V_fan_rtd_C)

    V_hs_dsgn_C = C_A['V_hs_dsgn_C'] if 'V_hs_dsgn_C' in C_A else get_V_hs_dsgn_C(C_A, q_rtd_C)
    """ 冷房時の送風機の設計風量[m3/h] """
    V_hs_dsgn_H: float = None  # NOTE: 冷房負荷計算時は空
    """ 暖房時の送風機の設計風量[m3/h] """

    E_UT_C_d_t: np.ndarray
    """冷房設備の未処理冷房負荷の設計一次エネルギー消費量相当値(MJ/h)"""

    E_UT_C_d_t, _, _, _, Theta_hs_out_d_t, Theta_hs_in_d_t, X_hs_out_d_t, X_hs_in_d_t, V_hs_supply_d_t, V_hs_vent_d_t, _\
        = calc_Q_UT_A(A_A, A_MR, A_OR, r_env, mu_H, mu_C,
            None, C_A['q_hs_rtd_C'], V_hs_dsgn_H, V_hs_dsgn_C, Q,
            C_A['VAV'], C_A['general_ventilation'], C_A['duct_insulation'], region, L_H_d_t_i, L_CS_d_t_i, L_CL_d_t_i)
    climate = load_climate(region)
    Theta_ex_d_t = get_Theta_ex(climate)

    E_E_C_d_t: np.ndarray
    """日付dの時刻tにおける1時間当たりの冷房時の消費電力量(kWh/h)"""

    E_E_C_d_t = calc_E_E_C_d_t(
        Theta_hs_out_d_t = Theta_hs_out_d_t,
        Theta_hs_in_d_t = Theta_hs_in_d_t,
        X_hs_out_d_t = X_hs_out_d_t,
        X_hs_in_d_t = X_hs_in_d_t,
        V_hs_supply_d_t = V_hs_supply_d_t,
        V_hs_vent_d_t = V_hs_vent_d_t,
        q_hs_rtd_C = C_A['q_hs_rtd_C'],
        V_hs_dsgn_C = V_hs_dsgn_C,
        q_hs_mid_C = C_A['q_hs_mid_C'],
        q_hs_min_C = C_A['q_hs_min_C'],
        P_fan_rtd_C = C_A['P_fan_rtd_C'],
        P_fan_mid_C = C_A['P_fan_mid_C'],
        P_hs_rtd_C = C_A['P_hs_rtd_C'],
        P_hs_mid_C = C_A['P_hs_mid_C'],
        V_fan_rtd_C = C_A['V_fan_rtd_C'],
        V_fan_mid_C = C_A['V_fan_mid_C'],
        EquipmentSpec = C_A['EquipmentSpec'],
        region = region)

    df_output2['E_UT_C_d_t_i [MJ/h']        = E_UT_C_d_t
    df_output2['Theta_hs_C_out_d_t [℃]']    = Theta_hs_out_d_t
    df_output2['Theta_hs_C_in_d_t [℃]']     = Theta_hs_in_d_t
    df_output2['Theta_ex_d_t [℃]']          = Theta_ex_d_t
    df_output2['V_hs_supply_C_d_t [m3/h]']  = V_hs_supply_d_t
    df_output2['V_hs_vent_C_d_t [m3/h]']    = V_hs_vent_d_t

    ##### 計算結果のまとめ
    #pprint.pprint(input_data)

    f_prim: float       = get_f_prim()                              #電気の量 1kWh を熱量に換算する係数(kJ/kWh)
    E_H_d_t: np.ndarray = E_E_H_d_t * f_prim / 1000 + E_UT_H_d_t    #1 時間当たりの暖房設備の設計一次エネルギー消費量(MJ/h)
    E_C_d_t: np.ndarray = E_E_C_d_t * f_prim / 1000 + E_UT_C_d_t    #1 時間当たりの冷房設備の設計一次エネルギー消費量(MJ/h)
    E_H                 = np.sum(E_H_d_t)                           #1 年当たりの暖房設備の設計一次エネルギー消費量(MJ/年)
    E_C                 = np.sum(E_C_d_t)                           #1 年当たりの冷房設備の設計一次エネルギー消費量(MJ/年)

    _logger.info(f"E_H [MJ/year]: {E_H}")
    _logger.info(f"E_C [MJ/year]: {E_C}")
    print('E_H [MJ/year]: ', E_H, ', E_C [MJ/year]: ', E_C)

    df_output1 = pd.DataFrame(index = ['合計値'])
    df_output1['E_H [MJ/year]'] = E_H
    df_output1['E_C [MJ/year]'] = E_C
    df_output1.to_csv(case_name + version_info() + '_output1.csv', encoding = 'cp932')

    df_output2['E_H_d_t [MJ/h]']            = E_H_d_t
    df_output2['E_C_d_t [MJ/h]']            = E_C_d_t
    df_output2['E_E_H_d_t [kWh/h]']         = E_E_H_d_t
    df_output2['E_E_C_d_t [kWh/h]']         = E_E_C_d_t
    df_output2['E_UT_H_d_t [MJ/h]']         = E_UT_H_d_t
    df_output2['E_UT_C_d_t [MJ/h]']         = E_UT_C_d_t
    df_output2['L_H_d_t [MJ/h]']            = L_H_d_t
    df_output2['L_CS_d_t [MJ/h]']           = L_CS_d_t
    df_output2['L_CL_d_t [MJ/h]']           = L_CL_d_t

    df_output2.to_csv(case_name + version_info() + '_output2.csv', encoding = 'cp932')

    # NOTE: 結合テストで確認したい値を返すのに使用します
    if test_mode:
        i = TestInputPickups(q_rtd_C, q_rtd_H, q_max_C, q_max_H, e_rtd_C, e_rtd_H)
        r = ResultSummary(E_C, E_H)
        # NOTE: 今後の拡張を想定して既存コードが壊れにくい辞書型にしています
        return {'TInput':i, 'TValue':r}
