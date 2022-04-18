# -*- coding: utf-8 -*-

import numpy as np
import json
import os
import sys

scriptDir = os.path.dirname(__file__)
sys.path.append(scriptDir + '/../src')

from pyhees.section2_1_b import get_f_prim

from pyhees.section4_1 import calc_heating_load, calc_cooling_load, get_virtual_heating_devices, get_alpha_UT_H_A, calc_E_E_H_hs_A_d_t, calc_E_E_C_hs_d_t
from pyhees.section4_1_a import calc_heating_mode

# ダクト式セントラル空調機
import pyhees.section4_2_b as dc_spec

# 床下
import pyhees.section3_1 as ld
from pyhees.section3_2 import calc_r_env, get_Q_dash, get_mu_H, get_mu_C

import jjj_experiment.calc
import jjj_experiment.constants
import jjj_experiment.input


"""# 基本条件の取得"""

# ---------- 計算条件の取得 ----------

# 引数が2つ与えられた場合、気象データと外気データを読み込む
if len(sys.argv) >= 3:
    climateFile = sys.argv[1]
    outdoorFile = sys.argv[2]
else:
    climateFile = '-'
    outdoorFile = '-'

# JSONの読み込み
rawInput = sys.stdin.read(-1)
input = json.loads(rawInput)

# 計算時の定数を取得
jjj_experiment.constants.set_constants(input)

# 基本情報を取得
type, tatekata, A_A, A_MR, A_OR, region, sol_region = jjj_experiment.input.get_basic(input)

# 外皮条件を取得
ENV, NV_MR, NV_OR, TS, r_A_ufvnt, underfloor_insulation, underfloor_air_conditioning_air_supply, hs_CAV = jjj_experiment.input.get_env(input)

# 暖房条件の取得
mode_H, H_A, H_MR, H_OR, H_HS = jjj_experiment.input.get_heating(input, region, A_A)

# 冷房条件の取得
mode_C, C_A, C_MR, C_OR = jjj_experiment.input.get_cooling(input, region, A_A)

# 熱交換型換気の取得
HEX = jjj_experiment.input.get_heatexchangeventilation()

# 太陽熱利用の取得
SHC = jjj_experiment.input.get_solarheat()

# セントラルルームエアコンディショナの性能の取得
q_rtd_C, q_rtd_H, q_max_C, q_max_H, e_rtd_C, e_rtd_H, dualcompressor_C, dualcompressor_H,\
    input_C_af_C, input_C_af_H = jjj_experiment.input.get_CRAC_spec(input)

# ---------- その他計算条件を取得 ----------

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

L_H_d_t_i, _ = calc_heating_load(region, sol_region, A_A, A_MR, A_OR, Q, mu_H, mu_C, NV_MR, NV_OR, TS, r_A_ufvnt,
                                     HEX, underfloor_insulation, mode_H, mode_C, spec_MR, spec_OR, mode_MR, mode_OR, SHC)
L_H_d_t: np.ndarray = np.sum(L_H_d_t_i, axis=0)
"""暖房負荷の全区画合計 [MJ/h]"""

##### 冷房負荷の取得（MJ/h）
L_CS_d_t_i: np.ndarray
"""冷房顕熱負荷 [MJ/h]"""
L_CL_d_t_i: np.ndarray
"""冷房潜熱負荷 [MJ/h]"""
L_CS_d_t_i, L_CL_d_t_i = calc_cooling_load(region, A_A, A_MR, A_OR, Q, mu_H, mu_C, NV_MR, NV_OR, r_A_ufvnt,
                                               underfloor_insulation, mode_C, mode_H, mode_MR, mode_OR, TS, HEX)
L_CS_d_t: np.ndarray = np.sum(L_CS_d_t_i, axis=0)
"""冷房顕熱負荷の全区画合計 [MJ/h]"""
L_CL_d_t: np.ndarray = np.sum(L_CL_d_t_i, axis=0)
"""冷房潜熱負荷の全区画合計 [MJ/h]"""

##### 暖房消費電力の計算（kWh/h）
V_rac_fan_rtd_H: float = dc_spec.get_V_fan_rtd_H(q_rtd_H)
"""定格暖房能力運転時の送風機の風量(m3/h)"""

if H_A['type'] == 'ダクト式セントラル空調機':
    if 'V_hs_dsgn_H' in H_A:
        V_hs_dsgn_H = H_A['V_hs_dsgn_H']
    else:
        V_hs_dsgn_H = dc_spec.get_V_fan_dsgn_C(H_A['V_fan_rtd_H'])
elif H_A['type'] == 'ルームエアコンディショナ活用型全館空調システム':
        V_hs_dsgn_H = dc_spec.get_V_fan_dsgn_C(V_rac_fan_rtd_H)
else: 
    raise Exception("暖房方式が不正です。")
"""暖房時の送風機の設計風量(m3/h)"""

P_rac_fan_rtd_H: float = dc_spec.get_P_fan_rtd_H(V_rac_fan_rtd_H)
"""定格暖房能力運転時の送風機の消費電力(W)"""

V_hs_dsgn_C: float = None
"""冷房時の送風機の設計風量(m3/h)"""

Q_UT_H_d_t_i: np.ndarray
"""暖房設備機器等の未処理暖房負荷(MJ/h)"""

E_E_H_d_t: np.ndarray
"""日付dの時刻tにおける1時間当たりの暖房時の消費電力量(kWh/h)"""

_, Q_UT_H_d_t_i, _, _, Theta_hs_out_d_t, Theta_hs_in_d_t, Theta_ex_d_t, _, _, V_hs_supply_d_t, V_hs_vent_d_t, C_df_H_d_t =\
    jjj_experiment.calc.calc_Q_UT_A(A_A, A_MR, A_OR, ENV['A_env'], mu_H, mu_C,
        H_A['q_hs_rtd_H'], None,
        q_rtd_H, q_rtd_C, q_max_H, q_max_C, V_hs_dsgn_H, V_hs_dsgn_C, Q, H_A['VAV'], H_A['general_ventilation'], hs_CAV,
        H_A['duct_insulation'], region, L_H_d_t_i, L_CS_d_t_i, L_CL_d_t_i,
        H_A['type'], input_C_af_H, input_C_af_C,
        underfloor_insulation, underfloor_air_conditioning_air_supply, YUCACO_r_A_ufvnt, climateFile, outdoorFile)

E_E_H_d_t: np.ndarray
"""日付dの時刻tにおける1時間当たりの暖房時の消費電力量(kWh/h)"""

E_E_H_d_t: np.ndarray = jjj_experiment.calc.calc_E_E_H_d_t(
    Theta_hs_out_d_t = Theta_hs_out_d_t,
    Theta_hs_in_d_t = Theta_hs_in_d_t,
    Theta_ex_d_t = Theta_ex_d_t,
    V_hs_supply_d_t = V_hs_supply_d_t,
    V_hs_vent_d_t = V_hs_vent_d_t,
    C_df_H_d_t = C_df_H_d_t,
    V_hs_dsgn_H = V_hs_dsgn_H,
    EquipmentSpec = H_A['EquipmentSpec'],
    q_hs_rtd_H = H_A['q_hs_rtd_H'],
    P_hs_rtd_H = H_A['P_hs_rtd_H'],
    V_fan_rtd_H = H_A['V_fan_rtd_H'],
    P_fan_rtd_H = H_A['P_fan_rtd_H'],
    q_hs_mid_H = H_A['q_hs_mid_H'],
    P_hs_mid_H = H_A['P_hs_mid_H'],
    V_fan_mid_H = H_A['V_fan_mid_H'],
    P_fan_mid_H = H_A['P_fan_mid_H'],
    q_hs_min_H = H_A['q_hs_min_H'],
    region = region,
    type = H_A['type'],
    q_rtd_C = q_rtd_C,
    q_rtd_H = q_rtd_H,
    P_rac_fan_rtd_H = P_rac_fan_rtd_H,
    e_rtd_H = e_rtd_H,
    dualcompressor_H = dualcompressor_H,
    input_C_af_H = input_C_af_H,
    f_SFP_H = H_A['f_SFP_H'])

alpha_UT_H_A: float = get_alpha_UT_H_A(region)
"""未処理暖房負荷を未処理暖房負荷の設計一次エネルギー消費量相当値に換算するための係数"""
Q_UT_H_A_d_t: np.ndarray = np.sum(Q_UT_H_d_t_i, axis=0)
"""未処理暖房負荷の全機器合計(MJ/h)"""
E_UT_H_d_t: np.ndarray = Q_UT_H_A_d_t * alpha_UT_H_A
"""未処理暖房負荷の設計一次エネルギー消費量相当値(MJ/h)"""

##### 冷房消費電力の計算（kWh/h）

V_fan_rtd_C: float = dc_spec.get_V_fan_rtd_C(q_rtd_C)
"""定格冷房能力運転時の送風機の風量(m3/h)"""

if C_A['type'] == 'ダクト式セントラル空調機':
    if 'V_hs_dsgn_C' in C_A:
        V_hs_dsgn_C = C_A['V_hs_dsgn_C']
    else:
        V_hs_dsgn_C = dc_spec.get_V_fan_dsgn_C(C_A['V_fan_rtd_C'])
elif C_A['type'] == 'ルームエアコンディショナ活用型全館空調システム':
    V_hs_dsgn_C = dc_spec.get_V_fan_dsgn_C(V_fan_rtd_C)
else: 
    raise Exception("冷房方式が不正です。")
"""冷房時の送風機の設計風量(m3/h)"""

P_rac_fan_rtd_C: float = dc_spec.get_P_fan_rtd_C(V_fan_rtd_C)
"""定格冷房能力運転時の送風機の消費電力(W)"""

V_hs_dsgn_H: float = None
"""暖房時の送風機の設計風量(m3/h)"""

E_C_UT_d_t: np.ndarray
"""冷房設備の未処理冷房負荷の設計一次エネルギー消費量相当値(MJ/h)"""

E_C_UT_d_t: np.ndarray
"""日付dの時刻tにおける1時間当たりの冷房時の消費電力量(kWh/h)"""

E_C_UT_d_t, _, _, _, Theta_hs_out_d_t, Theta_hs_in_d_t, Theta_ex_d_t, X_hs_out_d_t, X_hs_in_d_t, V_hs_supply_d_t, V_hs_vent_d_t, _\
    = jjj_experiment.calc.calc_Q_UT_A(A_A, A_MR, A_OR, ENV['A_env'], mu_H, mu_C,
        None, C_A['q_hs_rtd_C'],
        q_rtd_H, q_rtd_C, q_max_H, q_max_C, V_hs_dsgn_H, V_hs_dsgn_C, Q, C_A['VAV'], C_A['general_ventilation'], hs_CAV,
        C_A['duct_insulation'], region, L_H_d_t_i, L_CS_d_t_i, L_CL_d_t_i,
        C_A['type'], input_C_af_H, input_C_af_C,
        underfloor_insulation, underfloor_air_conditioning_air_supply, YUCACO_r_A_ufvnt, climateFile, outdoorFile)

E_E_C_d_t = jjj_experiment.calc.get_E_E_C_d_t(
    Theta_hs_out_d_t = Theta_hs_out_d_t,
    Theta_hs_in_d_t = Theta_hs_in_d_t,
    Theta_ex_d_t = Theta_ex_d_t,
    X_hs_out_d_t = X_hs_out_d_t,
    X_hs_in_d_t = X_hs_in_d_t,
    V_hs_supply_d_t = V_hs_supply_d_t,
    V_hs_vent_d_t = V_hs_vent_d_t,
    V_hs_dsgn_C = V_hs_dsgn_C,
    EquipmentSpec = C_A['EquipmentSpec'],
    q_hs_rtd_C = C_A['q_hs_rtd_C'],
    P_hs_rtd_C = C_A['P_hs_rtd_C'],
    V_fan_rtd_C = C_A['V_fan_rtd_C'],
    P_fan_rtd_C = C_A['P_fan_rtd_C'],
    q_hs_mid_C = C_A['q_hs_mid_C'],
    P_hs_mid_C = C_A['P_hs_mid_C'],
    V_fan_mid_C = C_A['V_fan_mid_C'],
    P_fan_mid_C = C_A['P_fan_mid_C'],
    q_hs_min_C = C_A['q_hs_min_C'],
    region = region,
    type = C_A['type'],
    q_rtd_C = q_rtd_C,
    e_rtd_C = e_rtd_C,
    P_rac_fan_rtd_C = P_rac_fan_rtd_C,
    dualcompressor_C = dualcompressor_C,
    input_C_af_C = input_C_af_C,
    f_SFP_C = C_A['f_SFP_C'])

##### 計算結果のまとめ

f_prim: float = get_f_prim()
"""電気の量 1kWh を熱量に換算する係数(kJ/kWh)"""

E_H_d_t: np.ndarray = E_E_H_d_t * f_prim / 1000 + E_UT_H_d_t
"""1 時間当たりの暖房設備の設計一次エネルギー消費量(MJ/h)"""

E_C_d_t: np.ndarray = E_E_C_d_t * f_prim / 1000 + E_C_UT_d_t
"""1 時間当たりの冷房設備の設計一次エネルギー消費量(MJ/h)"""

E_H = np.sum(E_H_d_t)
"""1 年当たりの暖房設備の設計一次エネルギー消費量(MJ/年)"""

E_C = np.sum(E_C_d_t)
"""1 年当たりの冷房設備の設計一次エネルギー消費量(MJ/年)"""

print(json.dumps({
    # 1年当たりの設計一次エネルギー消費量(MJ/年)
    'E_H': E_H,
    'E_C': E_C,

    # 1時間当たりの冷房設備の設計一次エネルギー消費量(MJ/h)
    'E_H_d_t': E_H_d_t.tolist(),
    'E_C_d_t': E_C_d_t.tolist(),

    # 1時間当たりの消費電力量(kWh/h)
    'E_E_H_d_t': E_E_H_d_t.tolist(),
    'E_E_C_d_t': E_E_C_d_t.tolist(),

    # 未処理負荷の設計一次エネルギー消費量相当値(MJ/h)
    'E_UT_H_d_t': E_UT_H_d_t.tolist(),
    'E_C_UT_d_t': E_C_UT_d_t.tolist(),

    # 負荷(MJ/h)
    'L_H_d_t': L_H_d_t.tolist(),
    'L_CS_d_t': L_CS_d_t.tolist(),
    'L_CL_d_t': L_CL_d_t.tolist(),
    }))