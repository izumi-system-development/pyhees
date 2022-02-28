# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
import json
import os
import sys
scriptDir = os.path.dirname(__file__)
sys.path.append(scriptDir + '/../src')

from pyhees.section2_1_b import get_f_prim

from pyhees.section4_1 import calc_heating_load, calc_cooling_load, get_virtual_heating_devices, get_alpha_UT_H_A
from pyhees.section4_1_a import calc_heating_mode

# ダクト式セントラル空調機
import pyhees.section4_2 as dc
import pyhees.section4_2_a as dc_a
import pyhees.section4_2_b as dc_spec

# エアーコンディショナー
import pyhees.section4_3 as rac
import pyhees.section4_3_a as rac_spec

# 床下
import pyhees.section3_1_e as uf
import pyhees.section3_1 as ld
from pyhees.section3_2 import calc_r_env, get_Q_dash, get_eta_H, get_eta_C
from pyhees.section3_2_8 import get_r_env
from pyhees.section11_1 import calc_h_ex

# 日付dの時刻tにおける1時間当たりの暖房時の消費電力量（kWh/h）(1)
def calc_CRAC_E_E_H_d_t(Theta_hs_out_d_t, Theta_hs_in_d_t, V_hs_supply_d_t, V_hs_vent_d_t, C_df_H_d_t,
           V_hs_dsgn_H, P_fan_rtd_H, region, q_rtd_C, q_rtd_H, e_rtd_H, dualcompressor_H):

    # (3)
    q_hs_H_d_t = dc_a.get_q_hs_H_d_t(Theta_hs_out_d_t, Theta_hs_in_d_t, V_hs_supply_d_t, C_df_H_d_t, region)

    E_E_CRAC_H_d_t = rac.calc_E_E_H_d_t(region, q_rtd_C, q_rtd_H, e_rtd_H, dualcompressor_H, q_hs_H_d_t * 3.6 / 1000)

    # (37)
    E_E_fan_H_d_t = dc_a.get_E_E_fan_H_d_t(P_fan_rtd_H, V_hs_vent_d_t, V_hs_supply_d_t, V_hs_dsgn_H, q_hs_H_d_t * 3.6 / 1000)

    # (1)
    E_E_H_d_t = E_E_CRAC_H_d_t + E_E_fan_H_d_t

    return E_E_H_d_t

def get_q_hs_C_d_t_2(Theta_hs_out_d_t, Theta_hs_in_d_t, X_hs_out_d_t, X_hs_in_d_t,V_hs_supply_d_t, region):
    """(4a-1)(4b-1)(4c-1)(4a-2)(4b-2)(4c-2)(4a-3)(4b-3)(4c-3)

    :param Theta_hs_out_d_t:日付dの時刻tにおける熱源機の出口における空気温度（℃）
    :param Theta_hs_in_d_t:日付dの時刻tにおける熱源機の入口における空気温度（℃）
    :param X_hs_out_d_t:日付dの時刻tにおける熱源機の出口における絶対湿度（kg/kg(DA)）
    :param X_hs_in_d_t:日付dの時刻tにおける熱源機の入口における絶対湿度（kg/kg(DA)）
    :param V_hs_supply_d_t:日付dの時刻tにおける熱源機の風量（m3/h）
    :param region:地域区分
    :return:日付dの時刻tにおける1時間当たりの熱源機の平均冷房能力（-）
    """
    H, C, M = dc_a.get_season_array_d_t(region)
    c_p_air = dc_a.get_c_p_air()
    rho_air = dc_a.get_rho_air()
    L_wtr = dc_a.get_L_wtr()

    # 暖房期および中間期 (4a-1)(4b-1)(4c-1)(4a-3)(4b-3)(4c-3)
    q_hs_C_d_t = np.zeros(24 * 365)
    q_hs_CS_d_t = np.zeros(24 * 365)
    q_hs_CL_d_t = np.zeros(24 * 365)

    # 冷房期 (4a-2)(4b-2)(4c-2)
    q_hs_CS_d_t[C] = np.clip(c_p_air * rho_air * (Theta_hs_in_d_t[C] - Theta_hs_out_d_t[C]) * (V_hs_supply_d_t[C] / 3600), 0, None)

    Cf = np.logical_and(C, q_hs_CS_d_t > 0)

    q_hs_CL_d_t[Cf] = np.clip(L_wtr * rho_air * (X_hs_in_d_t[Cf] - X_hs_out_d_t[Cf]) * (V_hs_supply_d_t[Cf] / 3600) * 10 ** 3, 0, None)

    return q_hs_CS_d_t, q_hs_CL_d_t

def get_CRAC_E_E_C_d_t(Theta_hs_out_d_t, Theta_hs_in_d_t,  X_hs_out_d_t, X_hs_in_d_t, V_hs_supply_d_t, V_hs_vent_d_t,
                  q_rtd_C, e_rtd_C, V_hs_dsgn_C, P_fan_rtd_C, region, dualcompressor_C):

    # 外気条件
    #outdoor = load_outdoor()
    outdoor = pd.read_csv('calc-experiment/outdoor_mitaka.csv', skiprows=4, nrows=24 * 365, names=(
    'day', 'hour', 'holiday', 'Theta_ex_1', 'X_ex_1'))

    #Theta_ex_d_t = get_Theta_ex(region, outdoor)
    Theta_ex_d_t = outdoor['Theta_ex_1'].values

    # (4)
    q_hs_CS_d_t, q_hs_CL_d_t = get_q_hs_C_d_t_2(Theta_hs_out_d_t, Theta_hs_in_d_t, X_hs_out_d_t, X_hs_in_d_t, V_hs_supply_d_t, region)

    E_E_CRAC_C_d_t = rac.calc_E_E_C_d_t(region, q_rtd_C, e_rtd_C, dualcompressor_C, q_hs_CS_d_t * 3.6 / 1000, q_hs_CL_d_t * 3.6 / 1000)

    # (38)
    E_E_fan_C_d_t = dc_a.get_E_E_fan_C_d_t(P_fan_rtd_C, V_hs_vent_d_t, V_hs_supply_d_t, V_hs_dsgn_C, q_hs_CS_d_t * 3.6 / 1000 + q_hs_CL_d_t * 3.6 / 1000)

    # (2)
    E_E_C_d_t = E_E_CRAC_C_d_t + E_E_fan_C_d_t

    return E_E_C_d_t

# 未処理負荷と機器の計算に必要な変数を取得
def calc_CRAC_Q_UT_A(A_A, A_MR, A_OR, A_env, mu_H, mu_C, q_rtd_C, q_rtd_H, q_max_C, q_max_H, V_hs_dsgn_H, V_hs_dsgn_C, Q,
             VAV, general_ventilation, duct_insulation, region, L_H_d_t_i, L_CS_d_t_i, L_CL_d_t_i):

    # 外気条件
    #outdoor = load_outdoor()

    outdoor = pd.read_csv('calc-experiment/outdoor_mitaka.csv', skiprows=4, nrows=24 * 365, names=(
    'day', 'hour', 'holiday', 'Theta_ex_1', 'X_ex_1'))

    #Theta_ex_d_t = get_Theta_ex(region, outdoor)
    #X_ex_d_t = get_X_ex(region, outdoor)
    Theta_ex_d_t = outdoor['Theta_ex_1'].values
    X_ex_d_t = outdoor['X_ex_1'].values

    #climate = load_climate(region)
    climate = pd.read_csv('calc-experiment/climateData_6_mitaka.csv', nrows=24 * 365)
    
    #J_d_t = get_J(climate)
    J_d_t = climate["水平面天空日射量 [W/m2]"].values
    h_ex_d_t = calc_h_ex(X_ex_d_t, Theta_ex_d_t)

    #主たる居室・その他居室・非居室の面積
    A_HCZ_i = np.array([ld.get_A_HCZ_i(i, A_A, A_MR, A_OR) for i in range(1, 6)])
    A_HCZ_R_i = [ld.get_A_HCZ_R_i(i) for i in range(1, 6)]
    A_NR = ld.get_A_NR(A_A, A_MR, A_OR)

    # (67)  水の蒸発潜熱
    L_wtr = dc.get_L_wtr()

    # (66d)　非居室の在室人数
    n_p_NR_d_t = dc.calc_n_p_NR_d_t(A_NR)

    # (66c)　その他居室の在室人数
    n_p_OR_d_t = dc.calc_n_p_OR_d_t(A_OR)

    # (66b)　主たる居室の在室人数
    n_p_MR_d_t = dc.calc_n_p_MR_d_t(A_MR)

    # (66a)　在室人数
    n_p_d_t = dc.get_n_p_d_t(n_p_MR_d_t, n_p_OR_d_t, n_p_NR_d_t)

    # 人体発熱
    q_p_H = dc.get_q_p_H()
    q_p_CS = dc.get_q_p_CS()
    q_p_CL = dc.get_q_p_CL()

    # (65d)　非居室の内部発湿
    w_gen_NR_d_t = dc.calc_w_gen_NR_d_t(A_NR)

    # (65c)　その他居室の内部発湿
    w_gen_OR_d_t = dc.calc_w_gen_OR_d_t(A_OR)

    # (65b)　主たる居室の内部発湿
    w_gen_MR_d_t = dc.calc_w_gen_MR_d_t(A_MR)

    # (65a)　内部発湿
    w_gen_d_t = dc.get_w_gen_d_t(w_gen_MR_d_t, w_gen_OR_d_t, w_gen_NR_d_t)

    # (64d)　非居室の内部発熱
    q_gen_NR_d_t = dc.calc_q_gen_NR_d_t(A_NR)

    # (64c)　その他居室の内部発熱
    q_gen_OR_d_t = dc.calc_q_gen_OR_d_t(A_OR)

    # (64b)　主たる居室の内部発熱
    q_gen_MR_d_t = dc.calc_q_gen_MR_d_t(A_MR)

    # (64a)　内部発熱
    q_gen_d_t = dc.get_q_gen_d_t(q_gen_MR_d_t, q_gen_OR_d_t, q_gen_NR_d_t)

    # (63)　局所排気量
    V_vent_l_NR_d_t = dc.get_V_vent_l_NR_d_t()
    V_vent_l_OR_d_t = dc.get_V_vent_l_OR_d_t()
    V_vent_l_MR_d_t = dc.get_V_vent_l_MR_d_t()
    V_vent_l_d_t = dc.get_V_vent_l_d_t(V_vent_l_MR_d_t, V_vent_l_OR_d_t, V_vent_l_NR_d_t)

    # (62)　全般換気量
    V_vent_g_i = dc.get_V_vent_g_i(A_HCZ_i, A_HCZ_R_i)

    # (61)　間仕切の熱貫流率
    U_prt = dc.get_U_prt()

    # (60)　非居室の間仕切の面積
    r_env = get_r_env(A_env, A_A)
    A_prt_i = dc.get_A_prt_i(A_HCZ_i, r_env, A_MR, A_NR, A_OR)

    # (59)　等価外気温度
    Theta_SAT_d_t = dc.get_Theta_SAT_d_t(Theta_ex_d_t, J_d_t)

    # (58)　断熱区画外を通るダクトの長さ
    l_duct_ex_i = dc.get_l_duct_ex_i(A_A)

    # (57)　断熱区画内を通るダクト長さ
    l_duct_in_i = dc.get_l_duct_in_i(A_A)

    # (56)　ダクト長さ
    l_duct_i = dc.get_l_duct__i(l_duct_in_i, l_duct_ex_i)

    # (51)　負荷バランス時の居室の絶対湿度
    X_star_HBR_d_t = dc.get_X_star_HBR_d_t(X_ex_d_t, region)

    # (50)　負荷バランス時の居室の室温
    Theta_star_HBR_d_t = dc.get_Theta_star_HBR_d_t(Theta_ex_d_t, region)

    # (55)　小屋裏の空気温度
    Theta_attic_d_t = dc.get_Theta_attic_d_t(Theta_SAT_d_t, Theta_star_HBR_d_t)

    # (54)　ダクトの周囲の空気温度
    Theta_sur_d_t_i = dc.get_Theta_sur_d_t_i(Theta_star_HBR_d_t, Theta_attic_d_t, l_duct_in_i, l_duct_ex_i, duct_insulation)

    # (40)　熱源機の風量を計算するための熱源機の出力
    Q_hat_hs_d_t = dc.calc_Q_hat_hs_d_t(Q, A_A, V_vent_l_d_t, V_vent_g_i, mu_H, mu_C, J_d_t, q_gen_d_t, n_p_d_t, q_p_H,
                                     q_p_CS, q_p_CL, X_ex_d_t, w_gen_d_t, Theta_ex_d_t, L_wtr, region)

    # (39)　熱源機の最低風量
    V_hs_min = dc.get_V_hs_min(V_vent_g_i)

    ####################################################################################################################
    # (38)　冷房時の熱源機の定格出力
    Q_hs_rtd_C = dc.get_Q_hs_rtd_C(q_rtd_C)             #ルームエアコンディショナの定格能力 q_rtd_C を入力するよう書き換え

    # (37)　暖房時の熱源機の定格出力
    Q_hs_rtd_H = dc.get_Q_hs_rtd_H(q_rtd_H)             #ルームエアコンディショナの定格能力 q_rtd_H を入力するよう書き換え
    ####################################################################################################################

    # (36)　VAV 調整前の熱源機の風量
    if CAV:
        H, C, M = dc_a.get_season_array_d_t(region)
        V_dash_hs_supply_d_t = np.zeros(24 * 365)
        V_dash_hs_supply_d_t[H] = V_hs_dsgn_H
        V_dash_hs_supply_d_t[C] = V_hs_dsgn_C
        V_dash_hs_supply_d_t[M] = (V_hs_dsgn_H + V_hs_dsgn_C) / 2
    else:
        V_dash_hs_supply_d_t = dc.get_V_dash_hs_supply_d_t(V_hs_min, V_hs_dsgn_H, V_hs_dsgn_C, Q_hs_rtd_H, Q_hs_rtd_C, Q_hat_hs_d_t, region)
    
    # (45)　風量バランス
    r_supply_des_i = dc.get_r_supply_des_i(A_HCZ_i)

    # (44)　VAV 調整前の吹き出し風量
    V_dash_supply_d_t_i = dc.get_V_dash_supply_d_t_i(r_supply_des_i, V_dash_hs_supply_d_t, V_vent_g_i)

    # (53)　負荷バランス時の非居室の絶対湿度
    X_star_NR_d_t = dc.get_X_star_NR_d_t(X_star_HBR_d_t, L_CL_d_t_i, L_wtr, V_vent_l_NR_d_t, V_dash_supply_d_t_i, region)

    # (52)　負荷バランス時の非居室の室温
    Theta_star_NR_d_t = dc.get_Theta_star_NR_d_t(Theta_star_HBR_d_t, Q, A_NR, V_vent_l_NR_d_t, V_dash_supply_d_t_i, U_prt,
                                              A_prt_i, L_H_d_t_i, L_CS_d_t_i, region)

    # (49)　実際の非居室の絶対湿度
    X_NR_d_t = dc.get_X_NR_d_t(X_star_NR_d_t)

    # (47)　実際の居室の絶対湿度
    X_HBR_d_t_i = dc.get_X_HBR_d_t_i(X_star_HBR_d_t)

    # (11)　熱損失を含む負荷バランス時の非居室への熱移動
    Q_star_trs_prt_d_t_i = dc.get_Q_star_trs_prt_d_t_i(U_prt, A_prt_i, Theta_star_HBR_d_t, Theta_star_NR_d_t)

    # (10)　熱取得を含む負荷バランス時の冷房潜熱負荷
    L_star_CL_d_t_i = dc.get_L_star_CL_d_t_i(L_CS_d_t_i, L_CL_d_t_i, region)

    # (9)　熱取得を含む負荷バランス時の冷房顕熱負荷
    L_star_CS_d_t_i = dc.get_L_star_CS_d_t_i(L_CS_d_t_i, Q_star_trs_prt_d_t_i, region)

    # (8)　熱損失を含む負荷バランス時の暖房負荷
    L_star_H_d_t_i = dc.get_L_star_H_d_t_i(L_H_d_t_i, Q_star_trs_prt_d_t_i, region)

    ####################################################################################################################
    # (24)　デフロストに関する暖房出力補正係数
    #C_df_H_d_t = dc.get_C_df_H_d_t(Theta_ex_d_t, h_ex_d_t)
    C_df_H_d_t = dc.get_C_df_H_d_t(30, h_ex_d_t)                                                                        #必ず1になるよう設定（暫定）

    # 最大暖房能力比
    q_r_max_H = rac.get_q_r_max_H(q_max_H, q_rtd_H)

    # 最大暖房出力比
    Q_r_max_H_d_t = rac.calc_Q_r_max_H_d_t(q_rtd_C, q_r_max_H, Theta_ex_d_t)

    # 最大暖房出力
    Q_max_H_d_t = rac.calc_Q_max_H_d_t(Q_r_max_H_d_t, q_rtd_H, Theta_ex_d_t, h_ex_d_t)
    Q_hs_max_H_d_t = Q_max_H_d_t

    # 最大冷房能力比
    q_r_max_C = rac.get_q_r_max_C(q_max_C, q_rtd_C)

    # 最大冷房出力比
    Q_r_max_C_d_t = rac.calc_Q_r_max_C_d_t(q_r_max_C, q_rtd_C, Theta_ex_d_t)

    # 最大冷房出力
    Q_max_C_d_t = rac.calc_Q_max_C_d_t(Q_r_max_C_d_t, q_rtd_C)

    # 冷房負荷最小顕熱比
    SHF_L_min_c = rac.get_SHF_L_min_c()

    # 最大冷房潜熱負荷
    L_max_CL_d_t = rac.get_L_max_CL_d_t(np.sum(L_CS_d_t_i, axis=0), SHF_L_min_c)

    # 補正冷房潜熱負荷
    L_dash_CL_d_t = rac.get_L_dash_CL_d_t(L_max_CL_d_t, np.sum(L_CL_d_t_i, axis=0))
    L_dash_C_d_t = rac.get_L_dash_C_d_t(np.sum(L_CS_d_t_i, axis=0), L_dash_CL_d_t)

    # 冷房負荷補正顕熱比
    SHF_dash_d_t = rac.get_SHF_dash_d_t(np.sum(L_CS_d_t_i, axis=0), L_dash_C_d_t)

    # 最大冷房顕熱出力, 最大冷房潜熱出力
    Q_max_CS_d_t = rac.get_Q_max_CS_d_t(Q_max_C_d_t, SHF_dash_d_t)
    Q_max_CL_d_t = rac.get_Q_max_CL_d_t(Q_max_C_d_t, SHF_dash_d_t, L_dash_CL_d_t)
    Q_hs_max_C_d_t = Q_max_C_d_t
    Q_hs_max_CL_d_t = Q_max_CL_d_t
    Q_hs_max_CS_d_t = Q_max_CS_d_t

    ####################################################################################################################

    # (20)　負荷バランス時の熱源機の入口における絶対湿度
    X_star_hs_in_d_t = dc.get_X_star_hs_in_d_t(X_star_NR_d_t)

    # (19)　負荷バランス時の熱源機の入口における空気温度
    Theta_star_hs_in_d_t = dc.get_Theta_star_hs_in_d_t(Theta_star_NR_d_t)

    # (18)　熱源機の出口における空気温度の最低値
    X_hs_out_min_C_d_t = dc.get_X_hs_out_min_C_d_t(X_star_hs_in_d_t, Q_hs_max_CL_d_t, V_dash_supply_d_t_i)

    # (22)　熱源機の出口における要求絶対湿度
    X_req_d_t_i = dc.get_X_req_d_t_i(X_star_HBR_d_t, L_star_CL_d_t_i, V_dash_supply_d_t_i, region)

    # (21)　熱源機の出口における要求空気温度
    Theta_req_d_t_i = dc.get_Theta_req_d_t_i(Theta_sur_d_t_i, Theta_star_HBR_d_t, V_dash_supply_d_t_i,
                        L_star_H_d_t_i, L_star_CS_d_t_i, l_duct_i, region)
    
    if YUCACO:
        Theta_uf_d_t, Theta_g_surf_d_t = uf.calc_Theta(region, A_A, A_MR, A_OR, Q, r_A_ufvnt, underfloor_insulation, Theta_req_d_t_i[0], Theta_ex_d_t,
                                                V_dash_supply_d_t_i[0], _, L_H_d_t_i, L_CS_d_t_i)
        Theta_req_d_t_i[0] += (Theta_req_d_t_i[0] - Theta_uf_d_t)
        Theta_uf_d_t, Theta_g_surf_d_t = uf.calc_Theta(region, A_A, A_MR, A_OR, Q, r_A_ufvnt, underfloor_insulation, Theta_req_d_t_i[1], Theta_ex_d_t,
                                                V_dash_supply_d_t_i[1], _, L_H_d_t_i, L_CS_d_t_i)
        Theta_req_d_t_i[1] += (Theta_req_d_t_i[1] - Theta_uf_d_t)

    # (15)　熱源機の出口における絶対湿度
    X_hs_out_d_t = dc.get_X_hs_out_d_t(X_NR_d_t, X_req_d_t_i, V_dash_supply_d_t_i, X_hs_out_min_C_d_t, L_star_CL_d_t_i, region)

    # 式(14)(46)(48)の条件に合わせてTheta_NR_d_tを初期化
    Theta_NR_d_t = np.zeros(24 * 365)

    # (17)　冷房時の熱源機の出口における空気温度の最低値
    Theta_hs_out_min_C_d_t = dc.get_Theta_hs_out_min_C_d_t(Theta_star_hs_in_d_t, Q_hs_max_CS_d_t, V_dash_supply_d_t_i)

    # (16)　暖房時の熱源機の出口における空気温度の最高値
    Theta_hs_out_max_H_d_t = dc.get_Theta_hs_out_max_H_d_t(Theta_star_hs_in_d_t, Q_hs_max_H_d_t, V_dash_supply_d_t_i)

    # L_star_H_d_t_i，L_star_CS_d_t_iの暖冷房区画1～5を合算し0以上だった場合の順序で計算
    # (14)　熱源機の出口における空気温度
    Theta_hs_out_d_t = dc.get_Theta_hs_out_d_t(VAV, Theta_req_d_t_i, V_dash_supply_d_t_i,
                                            L_star_H_d_t_i, L_star_CS_d_t_i, region, Theta_NR_d_t,
                                            Theta_hs_out_max_H_d_t, Theta_hs_out_min_C_d_t)

    # (43)　暖冷房区画𝑖の吹き出し風量
    V_supply_d_t_i = dc.get_V_supply_d_t_i(L_star_H_d_t_i, L_star_CS_d_t_i, Theta_sur_d_t_i, l_duct_i, Theta_star_HBR_d_t,
                                                    V_vent_g_i, V_dash_supply_d_t_i, VAV, region, Theta_hs_out_d_t)

    # (41)　暖冷房区画𝑖の吹き出し温度
    Theta_supply_d_t_i = dc.get_Thata_supply_d_t_i(Theta_sur_d_t_i, Theta_hs_out_d_t, Theta_star_HBR_d_t, l_duct_i,
                                                   V_supply_d_t_i, L_star_H_d_t_i, L_star_CS_d_t_i, region)

    if YUCACO:
        Theta_uf_d_t, Theta_g_surf_d_t = uf.calc_Theta(region, A_A, A_MR, A_OR, Q, r_A_ufvnt, underfloor_insulation, Theta_supply_d_t_i[0], Theta_ex_d_t,
                                                V_dash_supply_d_t_i[0], _, L_H_d_t_i, L_CS_d_t_i)
        Theta_supply_d_t_i[0] -= (Theta_supply_d_t_i[0] - Theta_uf_d_t)
        Theta_uf_d_t, Theta_g_surf_d_t = uf.calc_Theta(region, A_A, A_MR, A_OR, Q, r_A_ufvnt, underfloor_insulation, Theta_supply_d_t_i[1], Theta_ex_d_t,
                                                V_dash_supply_d_t_i[1], _, L_H_d_t_i, L_CS_d_t_i)
        Theta_supply_d_t_i[1] -= (Theta_supply_d_t_i[1] - Theta_uf_d_t)

    # (46)　暖冷房区画𝑖の実際の居室の室温
    Theta_HBR_d_t_i = dc.get_Theta_HBR_d_t_i(Theta_star_HBR_d_t, V_supply_d_t_i, Theta_supply_d_t_i, U_prt, A_prt_i, Q,
                                             A_HCZ_i, L_star_H_d_t_i, L_star_CS_d_t_i, region)

    # (48)　実際の非居室の室温
    Theta_NR_d_t = dc.get_Theta_NR_d_t(Theta_star_NR_d_t, Theta_star_HBR_d_t, Theta_HBR_d_t_i, A_NR, V_vent_l_NR_d_t,
                                        V_dash_supply_d_t_i, V_supply_d_t_i, U_prt, A_prt_i, Q)

    # L_star_H_d_t_i，L_star_CS_d_t_iの暖冷房区画1～5を合算し0以下だった場合の為に再計算
    # (14)　熱源機の出口における空気温度
    Theta_hs_out_d_t = dc.get_Theta_hs_out_d_t(VAV, Theta_req_d_t_i, V_dash_supply_d_t_i,
                                            L_star_H_d_t_i, L_star_CS_d_t_i, region, Theta_NR_d_t,
                                            Theta_hs_out_max_H_d_t, Theta_hs_out_min_C_d_t)

    # (42)　暖冷房区画𝑖の吹き出し絶対湿度
    X_supply_d_t_i = dc.get_X_supply_d_t_i(X_star_HBR_d_t, X_hs_out_d_t, L_star_CL_d_t_i, region)

    # (35)　熱源機の風量のうちの全般換気分
    V_hs_vent_d_t = dc.get_V_hs_vent_d_t(V_vent_g_i, general_ventilation)

    # (34)　熱源機の風量
    V_hs_supply_d_t = dc.get_V_hs_supply_d_t(V_supply_d_t_i)

    # (13)　熱源機の入口における絶対湿度
    X_hs_in_d_t = dc.get_X_hs_in_d_t(X_NR_d_t)

    # (12)　熱源機の入口における空気温度
    Theta_hs_in_d_t = dc.get_Theta_hs_in_d_t(Theta_NR_d_t)

    # (7)　間仕切りの熱取得を含む実際の冷房潜熱負荷
    L_dash_CL_d_t_i = dc.get_L_dash_CL_d_t_i(V_supply_d_t_i, X_HBR_d_t_i, X_supply_d_t_i, region)

    # (6)　間仕切りの熱取得を含む実際の冷房顕熱負荷
    L_dash_CS_d_t_i = dc.get_L_dash_CS_d_t_i(V_supply_d_t_i, Theta_supply_d_t_i, Theta_HBR_d_t_i, region)

    # (5)　間仕切りの熱損失を含む実際の暖房負荷
    L_dash_H_d_t_i = dc.get_L_dash_H_d_t_i(V_supply_d_t_i, Theta_supply_d_t_i, Theta_HBR_d_t_i, region)

    # (4)　冷房設備機器の未処理冷房潜熱負荷
    Q_UT_CL_d_t_i = dc.get_Q_UT_CL_d_t_i(L_star_CL_d_t_i, L_dash_CL_d_t_i)

    # (3)　冷房設備機器の未処理冷房顕熱負荷
    Q_UT_CS_d_t_i =dc. get_Q_UT_CS_d_t_i(L_star_CS_d_t_i, L_dash_CS_d_t_i)

    # (2)　暖房設備機器等の未処理暖房負荷
    Q_UT_H_d_t_i = dc.get_Q_UT_H_d_t_i(L_star_H_d_t_i, L_dash_H_d_t_i)

    # (1)　冷房設備の未処理冷房負荷の設計一次エネルギー消費量相当値
    E_C_UT_d_t = dc.get_E_C_UT_d_t(Q_UT_CL_d_t_i, Q_UT_CS_d_t_i, region)

    return E_C_UT_d_t, Q_UT_H_d_t_i, Q_UT_CS_d_t_i, Q_UT_CL_d_t_i, Theta_hs_out_d_t, Theta_hs_in_d_t, \
           X_hs_out_d_t, X_hs_in_d_t, V_hs_supply_d_t, V_hs_vent_d_t, C_df_H_d_t

def get_basic(input: dict):
    """基本情報の設定

    :return: 住宅タイプ、住宅建て方、床面積、地域区分、年間日射地域区分
    """
    # 住宅タイプ
    type = '一般住宅'

    # 住宅建て方
    tatekata = '戸建住宅'

    # 床面積
    A_A = input['A_A']
    A_MR = input['A_MR']
    A_OR = input['A_OR']

    # 地域区分
    region = input.region

    # 年間日射地域区分
    sol_region = None

    return type, tatekata, A_A, A_MR, A_OR, region, sol_region

def get_env(input: dict):
    """外皮の設定

    :return: 外皮条件
    """
    ENV = {
        'method': '当該住宅の外皮面積の合計を用いて評価する',
        'A_env': input['A_env'],
        'A_A': input['A_A'],
        'U_A': input['U_A'],
        'eta_A_H': input['eta_A_H'],
        'eta_A_C': input['eta_A_C']
    }

    # 自然風の利用 主たる居室
    NV_MR = 0
    # 自然風の利用 その他居室
    NV_OR = 0

    # 蓄熱
    TS = False

    # 床下空間を経由して外気を導入する換気方式の利用
    r_A_ufvnt = None

    # 床下空間の断熱
    underfloor_insulation = None

    return ENV, NV_MR, NV_OR, TS, r_A_ufvnt, underfloor_insulation

def get_heating(input: dict):
    """暖房の設定

    :return: 暖房方式、住戸全体の暖房条件、主たる居室の暖房機器、その他居室の暖房機器、温水暖房の種類
    """
    # 暖房方式
    mode_H = '住戸全体を連続的に暖房する方式'

    H_A = {
        'type': 'ダクト式セントラル空調機',
        'VAV': input['H_A']['VAV'] == 2,
        'general_ventilation': input['H_A']['general_ventilation'] == 2,
        'q_hs_rtd_H': input['H_A']['q_hs_rtd_H'],
        'P_hs_rtd_H': input['H_A']['P_hs_rtd_H'],
        'V_fan_rtd_H': input['H_A']['V_fan_rtd_H'],
        'P_fan_rtd_H': input['H_A']['P_fan_rtd_H'],
        'q_hs_mid_H': input['H_A']['q_hs_mid_H'],
        'P_hs_mid_H': input['H_A']['P_hs_mid_H'],
        'V_fan_mid_H': input['H_A']['V_fan_mid_H'],
        'P_fan_mid_H': input['H_A']['P_fan_mid_H']
    }

    # ダクトが通過する空間
    if input['H_A']['duct_insulation'] == 1:
        H_A['duct_insulation'] = '全てもしくは一部が断熱区画外である'
    elif input['H_A']['duct_insulation'] == 2:
        H_A['duct_insulation'] = '全て断熱区画内である'
    else:
        raise Exception('ダクトが通過する空間の入力が不正です。')

    # 機器の仕様の入力
    if input['H_A']['input'] == 1:
        H_A['EquipmentSpec'] = '入力しない'
    elif input['H_A']['input'] == 2:
        H_A['EquipmentSpec'] = '定格能力試験の値を入力する'
    elif input['H_A']['input'] == 3:
        H_A['EquipmentSpec'] = '定格能力試験と中間能力試験の値を入力する'
    else:
        raise Exception('機器の仕様の入力が不正です。')

    # 主たる居室暖房機器
    H_MR = None

    # その他居室暖房機器
    H_OR = None

    # 温水暖房機の種類
    H_HS = None

    return mode_H, H_A, H_MR, H_OR, H_HS

def get_cooling(input: dict):
    """冷房の設定

    :return: 冷房方式、住戸全体の冷房条件、主たる居室冷房条件、その他居室冷房条件
    """
    # 冷房方式
    mode_C = '住戸全体を連続的に冷房する方式'

    C_A = {
        'type': 'ダクト式セントラル空調機',
        'VAV': input['C_A']['VAV'] == 2,
        'general_ventilation': input['C_A']['general_ventilation'] == 2,
        'q_hs_rtd_C': input['C_A']['q_hs_rtd_C'],
        'P_hs_rtd_C': input['C_A']['P_hs_rtd_C'],
        'V_fan_rtd_C': input['C_A']['V_fan_rtd_C'],
        'P_fan_rtd_C': input['C_A']['P_fan_rtd_C'],
        'q_hs_mid_C': input['C_A']['q_hs_mid_C'],
        'P_hs_mid_C': input['C_A']['P_hs_mid_C'],
        'V_fan_mid_C': input['C_A']['V_fan_mid_C'],
        'P_fan_mid_C': input['C_A']['P_fan_mid_C']
    }

    # ダクトが通過する空間
    if input['C_A']['duct_insulation'] == 1:
        C_A['duct_insulation'] = '全てもしくは一部が断熱区画外である'
    elif input['C_A']['duct_insulation'] == 2:
        C_A['duct_insulation'] = '全て断熱区画内である'
    else:
        raise Exception('ダクトが通過する空間の入力が不正です。')

    # 機器の仕様の入力
    if input['C_A']['input'] == 1:
        C_A['EquipmentSpec'] = '入力しない'
    elif input['C_A']['input'] == 2:
        C_A['EquipmentSpec'] = '定格能力試験の値を入力する'
    elif input['C_A']['input'] == 3:
        C_A['EquipmentSpec'] = '定格能力試験と中間能力試験の値を入力する'
    else:
        raise Exception('機器の仕様の入力が不正です。')

    # 主たる居室冷房機器
    C_MR = None

    # その他居室冷房機器
    C_OR = None

    return mode_C, C_A, C_MR, C_OR

def get_CRAC_spec(input: dict):
    # エネルギー消費効率の入力（冷房）
    # 暖房は使われない
    e_class = None
    if input['C_A']['input_mode'] == 2:
        if input['C_A']['mode'] == 1:
            e_class = 'い'
        elif input['C_A']['mode'] == 2:
            e_class = 'ろ'
        elif input['C_A']['mode'] == 3:
            e_class = 'は'
        else:
            raise Exception('エネルギー消費効率の入力（冷房）が不正です。')

    # 定格冷房能力, 定格暖房能力
    q_rtd_C = 2800
    q_rtd_H = rac_spec.get_q_rtd_H(q_rtd_C)

    # 最大冷房能力, 最大暖房能力
    q_max_C = rac_spec.get_q_max_C(q_rtd_C)
    q_max_H = rac_spec.get_q_max_H(q_rtd_H, q_max_C)

    # 定格冷房エネルギー効率
    e_rtd_C = rac_spec.get_e_rtd_C(e_class, q_rtd_C)
    e_rtd_H = rac_spec.get_e_rtd_H(e_rtd_C)

    # 小能力時高効率型コンプレッサー
    dualcompressor_C = input['C_A']['dualcompressor'] == 2
    dualcompressor_H = input['H_A']['dualcompressor'] == 2

    return q_rtd_C, q_rtd_H, q_max_C, q_max_H, e_rtd_C, e_rtd_H, dualcompressor_C, dualcompressor_H

def get_heatexchangeventilation():
    """熱交換型換気の設定

    :return: 熱交換型換気
    """
    # 熱交換型換気
    HEX = None

    return HEX

def get_solarheat():
    """太陽熱利用の設定

    :return: 太陽熱利用
    """
    # 太陽熱利用
    SHC = None

    return SHC

"""# 基本条件の取得"""

# ---------- 計算条件の取得 ----------

# JSONの読み込み
input = json.loads(input())

# 基本情報を取得
type, tatekata, A_A, A_MR, A_OR, region, sol_region = get_basic(input)

# 外皮条件を取得
ENV, NV_MR, NV_OR, TS, r_A_ufvnt, underfloor_insulation = get_env(input)

# 暖房条件の取得
mode_H, H_A, H_MR, H_OR, H_HS = get_heating(input)

# 冷房条件の取得
mode_C, C_A, C_MR, C_OR = get_cooling(input)

# 熱交換型換気の取得
HEX = get_heatexchangeventilation()

# 太陽熱利用の取得
SHC = get_solarheat()

# セントラルルームエアコンディショナの性能の取得
q_rtd_C, q_rtd_H, q_max_C, q_max_H, e_rtd_C, e_rtd_H, dualcompressor_C, dualcompressor_H = get_CRAC_spec(input)

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
mu_H = get_eta_H(ENV['eta_A_H'], r_env)
mu_C = get_eta_C(ENV['eta_A_C'], r_env)

# 実質的な暖房機器の仕様を取得
spec_MR, spec_OR = get_virtual_heating_devices(region, H_MR, H_OR)

# 暖房方式及び運転方法の区分
mode_MR, mode_OR = calc_heating_mode(region=region, H_MR=spec_MR, H_OR=spec_OR)

YUCACO = True

if YUCACO:
    CAV = True
    r_A_ufvnt = (8.28+16.56+21.53) / (9.52+1.24+3.31+3.31+1.66+8.28+16.56+21.53) 
    underfloor_insulation = True       #床下断熱あり
else:
    CAV = True
    r_A_ufvnt = None
    underfloor_insulation = False

##### 暖房負荷の取得（MJ/h）

L_H_d_t_i: np.ndarray
"""暖房負荷 [MJ/h]"""

L_H_d_t_i, _ = calc_heating_load(region, sol_region, A_A, A_MR, A_OR, Q, mu_H, mu_C, NV_MR, NV_OR, TS, r_A_ufvnt,
                                     HEX, underfloor_insulation, mode_H, mode_C, spec_MR, spec_OR, mode_MR, mode_OR, SHC)

##### 冷房負荷の取得（MJ/h）
L_CS_d_t_i: np.ndarray
"""冷房顕熱負荷 [MJ/h]"""
L_CL_d_t_i: np.ndarray
"""冷房潜熱負荷 [MJ/h]"""
L_CS_d_t_i, L_CL_d_t_i = calc_cooling_load(region, A_A, A_MR, A_OR, Q, mu_H, mu_C, NV_MR, NV_OR, r_A_ufvnt,
                                               underfloor_insulation, mode_C, mode_H, mode_MR, mode_OR, TS, HEX)

##### 暖房消費電力の計算（kWh/h）
V_fan_rtd_H: float = dc_spec.get_V_fan_rtd_H(q_rtd_H)
"""定格暖房能力運転時の送風機の風量(m3/h)"""
V_hs_dsgn_H: float = dc_spec.get_V_fan_dsgn_H(V_fan_rtd_H)
"""暖房時の送風機の設計風量(m3/h)"""
P_fan_rtd_H: float = dc_spec.get_P_fan_rtd_H(V_fan_rtd_H)
"""定格暖房能力運転時の送風機の消費電力(W)"""

V_hs_dsgn_C: float = 0
"""冷房時の送風機の設計風量(m3/h)"""

Q_UT_H_d_t_i: np.ndarray
"""暖房設備機器等の未処理暖房負荷(MJ/h)"""
_, Q_UT_H_d_t_i, _, _, Theta_hs_out_d_t, Theta_hs_in_d_t, _, _, V_hs_supply_d_t, V_hs_vent_d_t, C_df_H_d_t\
 = calc_CRAC_Q_UT_A(A_A, A_MR, A_OR, ENV['A_env'], mu_H, mu_C,
                    q_rtd_C, q_rtd_H, q_max_C, q_max_H, V_hs_dsgn_H, V_hs_dsgn_C, Q, H_A['VAV'], H_A['general_ventilation'],
                    H_A['duct_insulation'], region, L_H_d_t_i, L_CS_d_t_i, L_CL_d_t_i)

E_E_H_d_t: np.ndarray = calc_CRAC_E_E_H_d_t(
    Theta_hs_out_d_t = Theta_hs_out_d_t,
    Theta_hs_in_d_t = Theta_hs_in_d_t,
    V_hs_supply_d_t = V_hs_supply_d_t,
    V_hs_vent_d_t = V_hs_vent_d_t,
    C_df_H_d_t = C_df_H_d_t,
    V_hs_dsgn_H = V_hs_dsgn_H,
    P_fan_rtd_H = P_fan_rtd_H,
    region = region,
    q_rtd_C = q_rtd_C,
    q_rtd_H = q_rtd_H,
    e_rtd_H = e_rtd_H,
    dualcompressor_H = dualcompressor_H)
"""日付dの時刻tにおける1時間当たりの暖房時の消費電力量(kWh/h)"""

alpha_UT_H_A: float = get_alpha_UT_H_A(region)
"""未処理暖房負荷を未処理暖房負荷の設計一次エネルギー消費量相当値に換算するための係数"""
Q_UT_H_A_d_t: np.ndarray = np.sum(Q_UT_H_d_t_i, axis=0)
"""未処理暖房負荷の全機器合計(MJ/h)"""
E_UT_H_d_t: np.ndarray = Q_UT_H_A_d_t * alpha_UT_H_A
"""未処理暖房負荷の設計一次エネルギー消費量相当値(MJ/h)"""

##### 冷房消費電力の計算（kWh/h）

V_fan_rtd_C = dc_spec.get_V_fan_rtd_C(q_rtd_C)
"""定格冷房能力運転時の送風機の風量(m3/h)"""
V_hs_dsgn_C = dc_spec.get_V_fan_dsgn_C(V_fan_rtd_C)
"""冷房時の送風機の設計風量(m3/h)"""
P_fan_rtd_C = dc_spec.get_P_fan_rtd_C(V_fan_rtd_C)
"""定格冷房能力運転時の送風機の消費電力(W)"""

V_hs_dsgn_H = 0
"""暖房時の送風機の設計風量(m3/h)"""

E_C_UT_d_t: np.ndarray
"""冷房設備の未処理冷房負荷の設計一次エネルギー消費量相当値(MJ/h)"""
E_C_UT_d_t, _, _, _, Theta_hs_out_d_t, Theta_hs_in_d_t, X_hs_out_d_t, X_hs_in_d_t, V_hs_supply_d_t, V_hs_vent_d_t, _\
= calc_CRAC_Q_UT_A(A_A, A_MR, A_OR, ENV['A_env'], mu_H, mu_C, 
                   q_rtd_C, q_rtd_H, q_max_C, q_max_H, V_hs_dsgn_H, V_hs_dsgn_C, Q, C_A['VAV'], C_A['general_ventilation'],
                   C_A['duct_insulation'], region, L_H_d_t_i, L_CS_d_t_i, L_CL_d_t_i)

E_E_C_d_t = get_CRAC_E_E_C_d_t(
    Theta_hs_out_d_t = Theta_hs_out_d_t,
    Theta_hs_in_d_t = Theta_hs_in_d_t,
    X_hs_out_d_t = X_hs_out_d_t,
    X_hs_in_d_t = X_hs_in_d_t,
    V_hs_supply_d_t = V_hs_supply_d_t,
    V_hs_vent_d_t = V_hs_vent_d_t,
    q_rtd_C = q_rtd_C,
    e_rtd_C = e_rtd_C,
    V_hs_dsgn_C = V_hs_dsgn_C,
    P_fan_rtd_C = P_fan_rtd_C,
    region = region,
    dualcompressor_C = dualcompressor_C)
"""日付dの時刻tにおける1時間当たりの冷房時の消費電力量(kWh/h)"""

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
    'E_H': E_H,
    'E_H_d_t': E_H_d_t.tolist(),
    'E_C': E_C,
    'E_C_d_t': E_C_d_t.tolist()
    }))