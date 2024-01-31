import numpy as np
import pandas as pd
from datetime import datetime

from pyhees.section11_1 import calc_h_ex, load_climate, get_Theta_ex, get_X_ex, get_climate_df
from pyhees.section11_2 import calc_I_s_d_t

# ダクト式セントラル空調機
import pyhees.section4_2 as dc
import pyhees.section4_2_a as dc_a
from jjjexperiment.constants import PROCESS_TYPE_1, PROCESS_TYPE_2, PROCESS_TYPE_3, PROCESS_TYPE_4

# エアーコンディショナー
import pyhees.section4_3 as rac

# 床下
# import pyhees.section3_1_e2 as uf
import pyhees.section3_1_e as uf
import pyhees.section3_1 as ld

from jjjexperiment.denchu_1 import Spec
import jjjexperiment.denchu_2 as denchu_2

import jjjexperiment.constants as constants
from jjjexperiment.logger import LimitedLoggerAdapter as _logger  # デバッグ用ロガー
from jjjexperiment.options import *

def version_info() -> str:
    """ 最終編集日をバージョン管理に使用します
    """
    # NOTE: subprocessモジュールによるコミット履歴からの生成は \
    # ipynb 環境では正常に動作しませんでした(returned no-zero exit status 128.)
    return '_20231025'

def calc_Q_UT_A(case_name, A_A, A_MR, A_OR, r_env, mu_H, mu_C, q_hs_rtd_H, q_hs_rtd_C, q_rtd_H, q_rtd_C, q_max_H, q_max_C, V_hs_dsgn_H, V_hs_dsgn_C, Q,
            VAV, general_ventilation, hs_CAV, duct_insulation, region, L_H_d_t_i, L_CS_d_t_i, L_CL_d_t_i,
            type, input_C_af_H, input_C_af_C, underfloor_insulation, underfloor_air_conditioning_air_supply, YUCACO_r_A_ufvnt, R_g, climateFile):
    """未処理負荷と機器の計算に必要な変数を取得"""

    df_output  = pd.DataFrame(index = pd.date_range(datetime(2023,1,1,1,0,0), datetime(2024,1,1,0,0,0), freq='h'))
    df_output2 = pd.DataFrame()
    df_output3 = pd.DataFrame()

    # 気象条件
    if climateFile == '-':
        climate = load_climate(region)
    else:
        climate = pd.read_csv(climateFile, nrows=24 * 365, encoding="SHIFT-JIS")
    Theta_ex_d_t = get_Theta_ex(climate)
    X_ex_d_t = get_X_ex(climate)
    J_d_t = calc_I_s_d_t(0, 0, get_climate_df(climate))
    h_ex_d_t = calc_h_ex(X_ex_d_t, Theta_ex_d_t)

    df_output['Theta_ex_d_t']  = Theta_ex_d_t
    df_output['X_ex_d_t']      = X_ex_d_t

    h_ex_d_t = calc_h_ex(X_ex_d_t, Theta_ex_d_t)

    df_output['J_d_t']         = J_d_t
    df_output['h_ex_d_t']      = h_ex_d_t

    #主たる居室・その他居室・非居室の面積
    A_HCZ_i = np.array([ld.get_A_HCZ_i(i, A_A, A_MR, A_OR) for i in range(1, 6)])
    A_HCZ_R_i = [ld.get_A_HCZ_R_i(i) for i in range(1, 6)]
    A_NR = ld.get_A_NR(A_A, A_MR, A_OR)

    df_output2['A_HCZ_i'] = A_HCZ_i
    df_output2['A_HCZ_R_i'] = A_HCZ_R_i
    df_output3['A_NR'] = [A_NR]

    # (67)  水の蒸発潜熱
    L_wtr = dc.get_L_wtr()
    df_output3['L_wtr'] = [L_wtr]

    # (66d)　非居室の在室人数
    n_p_NR_d_t = dc.calc_n_p_NR_d_t(A_NR)
    df_output['n_p_NR_d_t'] = n_p_NR_d_t

    # (66c)　その他居室の在室人数
    n_p_OR_d_t = dc.calc_n_p_OR_d_t(A_OR)
    df_output['n_p_OR_d_t'] = n_p_OR_d_t

    # (66b)　主たる居室の在室人数
    n_p_MR_d_t = dc.calc_n_p_MR_d_t(A_MR)
    df_output['n_p_MR_d_t'] = n_p_MR_d_t

    # (66a)　在室人数
    n_p_d_t = dc.get_n_p_d_t(n_p_MR_d_t, n_p_OR_d_t, n_p_NR_d_t)
    df_output['n_p_d_t'] = n_p_d_t

    # 人体発熱
    q_p_H = dc.get_q_p_H()
    q_p_CS = dc.get_q_p_CS()
    q_p_CL = dc.get_q_p_CL()
    df_output3['q_p_H'] = [q_p_H]
    df_output3['q_p_CS'] = [q_p_CS]
    df_output3['q_p_CL'] = [q_p_CL]

    # (65d)　非居室の内部発湿
    w_gen_NR_d_t = dc.calc_w_gen_NR_d_t(A_NR)
    df_output['w_gen_NR_d_t'] = w_gen_NR_d_t

    # (65c)　その他居室の内部発湿
    w_gen_OR_d_t = dc.calc_w_gen_OR_d_t(A_OR)
    df_output['w_gen_OR_d_t'] = w_gen_OR_d_t

    # (65b)　主たる居室の内部発湿
    w_gen_MR_d_t = dc.calc_w_gen_MR_d_t(A_MR)
    df_output['w_gen_MR_d_t'] = w_gen_MR_d_t

    # (65a)　内部発湿
    w_gen_d_t = dc.get_w_gen_d_t(w_gen_MR_d_t, w_gen_OR_d_t, w_gen_NR_d_t)
    df_output['w_gen_d_t'] = w_gen_d_t

    # (64d)　非居室の内部発熱
    q_gen_NR_d_t = dc.calc_q_gen_NR_d_t(A_NR)
    df_output['q_gen_NR_d_t'] = q_gen_NR_d_t

    # (64c)　その他居室の内部発熱
    q_gen_OR_d_t = dc.calc_q_gen_OR_d_t(A_OR)
    df_output['q_gen_OR_d_t'] = q_gen_OR_d_t

    # (64b)　主たる居室の内部発熱
    q_gen_MR_d_t = dc.calc_q_gen_MR_d_t(A_MR)
    df_output['q_gen_MR_d_t'] = q_gen_MR_d_t

    # (64a)　内部発熱
    q_gen_d_t = dc.get_q_gen_d_t(q_gen_MR_d_t, q_gen_OR_d_t, q_gen_NR_d_t)
    df_output['q_gen_d_t'] = q_gen_d_t

    # (63)　局所排気量
    V_vent_l_NR_d_t = dc.get_V_vent_l_NR_d_t()
    V_vent_l_OR_d_t = dc.get_V_vent_l_OR_d_t()
    V_vent_l_MR_d_t = dc.get_V_vent_l_MR_d_t()
    V_vent_l_d_t = dc.get_V_vent_l_d_t(V_vent_l_MR_d_t, V_vent_l_OR_d_t, V_vent_l_NR_d_t)
    df_output = df_output.assign(
        V_vent_l_NR_d_t = V_vent_l_NR_d_t,
        V_vent_l_OR_d_t = V_vent_l_OR_d_t,
        V_vent_l_MR_d_t = V_vent_l_MR_d_t,
        V_vent_l_d_t = V_vent_l_d_t
    )

    # (62)　全般換気量
    V_vent_g_i = dc.get_V_vent_g_i(A_HCZ_i, A_HCZ_R_i)
    df_output2['V_vent_g_i'] = V_vent_g_i

    # (61)　間仕切の熱貫流率
    U_prt = dc.get_U_prt()
    df_output3['U_prt'] = [U_prt]

    # (60)　非居室の間仕切の面積
    A_prt_i = dc.get_A_prt_i(A_HCZ_i, r_env, A_MR, A_NR, A_OR)
    df_output3['r_env'] = [r_env]
    df_output2['A_prt_i'] = A_prt_i

    # (59)　等価外気温度
    Theta_SAT_d_t = dc.get_Theta_SAT_d_t(Theta_ex_d_t, J_d_t)
    df_output['Theta_SAT_d_t'] = Theta_SAT_d_t

    # (58)　断熱区画外を通るダクトの長さ
    l_duct_ex_i = dc.get_l_duct_ex_i(A_A)
    df_output2['l_duct_ex_i'] = l_duct_ex_i

    # (57)　断熱区画内を通るダクト長さ
    l_duct_in_i = dc.get_l_duct_in_i(A_A)
    df_output2['l_duct_in_i'] = l_duct_in_i

    # (56)　ダクト長さ
    l_duct_i = dc.get_l_duct__i(l_duct_in_i, l_duct_ex_i)
    df_output2['l_duct_i'] = l_duct_i

    # (51)　負荷バランス時の居室の絶対湿度
    X_star_HBR_d_t = dc.get_X_star_HBR_d_t(X_ex_d_t, region)  # X_ex_d_t [g/kg(DA)] 想定
    df_output['X_star_HBR_d_t'] = X_star_HBR_d_t

    # (50)　負荷バランス時の居室の室温
    Theta_star_HBR_d_t = dc.get_Theta_star_HBR_d_t(Theta_ex_d_t, region)
    df_output['Theta_star_HBR_d_t'] = Theta_star_HBR_d_t

    # (55)　小屋裏の空気温度
    Theta_attic_d_t = dc.get_Theta_attic_d_t(Theta_SAT_d_t, Theta_star_HBR_d_t)
    df_output['Theta_attic_d_t'] = Theta_attic_d_t

    # (54)　ダクトの周囲の空気温度
    Theta_sur_d_t_i = dc.get_Theta_sur_d_t_i(Theta_star_HBR_d_t, Theta_attic_d_t, l_duct_in_i, l_duct_ex_i, duct_insulation)
    df_output = df_output.assign(
        Theta_sur_d_t_i_1 = Theta_sur_d_t_i[0],
        Theta_sur_d_t_i_2 = Theta_sur_d_t_i[1],
        Theta_sur_d_t_i_3 = Theta_sur_d_t_i[2],
        Theta_sur_d_t_i_4 = Theta_sur_d_t_i[3],
        Theta_sur_d_t_i_5 = Theta_sur_d_t_i[4]
    )

    # (40)　熱源機の風量を計算するための熱源機の出力
    # NOTE: 潜熱バグフィックスが有効でないと誤った数字となります
    Q_hat_hs_d_t, Q_hat_hs_CS_d_t = dc.calc_Q_hat_hs_d_t(Q, A_A, V_vent_l_d_t, V_vent_g_i, mu_H, mu_C, J_d_t, q_gen_d_t, n_p_d_t, q_p_H,
                                     q_p_CS, q_p_CL, X_ex_d_t, w_gen_d_t, Theta_ex_d_t, L_wtr, region)
    df_output['Q_hat_hs_d_t'] = Q_hat_hs_d_t

    # (39)　熱源機の最低風量
    V_hs_min = dc.get_V_hs_min(V_vent_g_i)
    df_output3['V_hs_min'] = [V_hs_min]

    ####################################################################################################################
    if type == PROCESS_TYPE_1 or type == PROCESS_TYPE_3:
        # (38)
        Q_hs_rtd_C = dc.get_Q_hs_rtd_C(q_hs_rtd_C)

        # (37)
        Q_hs_rtd_H = dc.get_Q_hs_rtd_H(q_hs_rtd_H)
    elif type == PROCESS_TYPE_2 or type == PROCESS_TYPE_4:
        # (38)　冷房時の熱源機の定格出力
        Q_hs_rtd_C = dc.get_Q_hs_rtd_C(q_rtd_C)  #ルームエアコンディショナの定格能力 q_rtd_C を入力するよう書き換え

        # (37)　暖房時の熱源機の定格出力
        Q_hs_rtd_H = dc.get_Q_hs_rtd_H(q_rtd_H)  #ルームエアコンディショナの定格能力 q_rtd_H を入力するよう書き換え
    else:
        raise Exception('設備機器の種類の入力が不正です。')

    df_output3['Q_hs_rtd_C'] = [Q_hs_rtd_C]
    df_output3['Q_hs_rtd_H'] = [Q_hs_rtd_H]
    ####################################################################################################################

    # (36)　VAV 調整前の熱源機の風量
    if hs_CAV:
        H, C, M = dc_a.get_season_array_d_t(region)
        V_dash_hs_supply_d_t = np.zeros(24 * 365)
        V_dash_hs_supply_d_t[H] = V_hs_dsgn_H or 0
        V_dash_hs_supply_d_t[C] = V_hs_dsgn_C or 0
        V_dash_hs_supply_d_t[M] = 0
    else:
        if Q_hs_rtd_H is not None:
            updated_V_hs_dsgn_H = V_hs_dsgn_H or 0
        else:
            updated_V_hs_dsgn_H = None
        if Q_hs_rtd_C is not None:
            updated_V_hs_dsgn_C = V_hs_dsgn_C or 0
        else:
            updated_V_hs_dsgn_C = None

        if type == PROCESS_TYPE_3:
            # FIXME: 方式3が他方式と比較して大きくなる問題
            if updated_V_hs_dsgn_C is not None:
                # 冷房時 => 顕熱負荷のみ
                V_dash_hs_supply_d_t = dc.get_V_dash_hs_supply_d_t_2023(Q_hat_hs_CS_d_t, region, True)
            else:
                # 暖房 => 全熱負荷
                V_dash_hs_supply_d_t = dc.get_V_dash_hs_supply_d_t_2023(Q_hat_hs_d_t, region, True)
            df_output['V_dash_hs_supply_d_t'] = V_dash_hs_supply_d_t
        else:
            V_dash_hs_supply_d_t = dc.get_V_dash_hs_supply_d_t(V_hs_min, updated_V_hs_dsgn_H, updated_V_hs_dsgn_C, Q_hs_rtd_H, Q_hs_rtd_C, Q_hat_hs_d_t, region)
            df_output['V_dash_hs_supply_d_t'] = V_dash_hs_supply_d_t

    if VAV and constants.change_supply_volume_before_vav_adjust == VAVありなしの吹出風量.数式を統一する.value:
        # (45)　風量バランス
        r_supply_des_d_t_i = dc.get_r_supply_des_d_t_i_2023(region, L_CS_d_t_i, L_H_d_t_i)
        # (44)　VAV 調整前の吹き出し風量
        V_dash_supply_d_t_i = dc.get_V_dash_supply_d_t_i_2023(r_supply_des_d_t_i, V_dash_hs_supply_d_t, V_vent_g_i)

        df_output2['r_supply_des_i'] = None
        df_output = df_output.assign(
            r_supply_des_d_t_1 = r_supply_des_d_t_i[0],
            r_supply_des_d_t_2 = r_supply_des_d_t_i[1],
            r_supply_des_d_t_3 = r_supply_des_d_t_i[2],
            r_supply_des_d_t_4 = r_supply_des_d_t_i[3],
            r_supply_des_d_t_5 = r_supply_des_d_t_i[4]
        )
    else:
        # (45)　風量バランス
        r_supply_des_i = dc.get_r_supply_des_i(A_HCZ_i)
        # (44)　VAV 調整前の吹き出し風量
        V_dash_supply_d_t_i = dc.get_V_dash_supply_d_t_i(r_supply_des_i, V_dash_hs_supply_d_t, V_vent_g_i)

        df_output2['r_supply_des_i'] = r_supply_des_i
        df_output = df_output.assign(
            r_supply_des_d_t_1 = None,
            r_supply_des_d_t_2 = None,
            r_supply_des_d_t_3 = None,
            r_supply_des_d_t_4 = None,
            r_supply_des_d_t_5 = None
        )
    df_output = df_output.assign(
        V_dash_supply_d_t_1 = V_dash_supply_d_t_i[0],
        V_dash_supply_d_t_2 = V_dash_supply_d_t_i[1],
        V_dash_supply_d_t_3 = V_dash_supply_d_t_i[2],
        V_dash_supply_d_t_4 = V_dash_supply_d_t_i[3],
        V_dash_supply_d_t_5 = V_dash_supply_d_t_i[4]
    )

    # (53)　負荷バランス時の非居室の絶対湿度
    X_star_NR_d_t = dc.get_X_star_NR_d_t(X_star_HBR_d_t, L_CL_d_t_i, L_wtr, V_vent_l_NR_d_t, V_dash_supply_d_t_i, region)
    df_output['X_star_NR_d_t'] = X_star_NR_d_t

    # (52)　負荷バランス時の非居室の室温
    Theta_star_NR_d_t = dc.get_Theta_star_NR_d_t(Theta_star_HBR_d_t, Q, A_NR, V_vent_l_NR_d_t, V_dash_supply_d_t_i, U_prt,
                                              A_prt_i, L_H_d_t_i, L_CS_d_t_i, region)
    df_output['Theta_star_NR_d_t'] = Theta_star_NR_d_t

    # (49)　実際の非居室の絶対湿度
    X_NR_d_t = dc.get_X_NR_d_t(X_star_NR_d_t)
    df_output['X_NR_d_t'] = X_NR_d_t

    # (47)　実際の居室の絶対湿度
    X_HBR_d_t_i = dc.get_X_HBR_d_t_i(X_star_HBR_d_t)
    df_output = df_output.assign(
        X_HBR_d_t_1 = X_HBR_d_t_i[0],
        X_HBR_d_t_2 = X_HBR_d_t_i[1],
        X_HBR_d_t_3 = X_HBR_d_t_i[2],
        X_HBR_d_t_4 = X_HBR_d_t_i[3],
        X_HBR_d_t_5 = X_HBR_d_t_i[4]
    )

    # (11)　熱損失を含む負荷バランス時の非居室への熱移動
    Q_star_trs_prt_d_t_i = dc.get_Q_star_trs_prt_d_t_i(U_prt, A_prt_i, Theta_star_HBR_d_t, Theta_star_NR_d_t)
    df_output = df_output.assign(
        Q_star_trs_prt_d_t_i_1 = Q_star_trs_prt_d_t_i[0],
        Q_star_trs_prt_d_t_i_2 = Q_star_trs_prt_d_t_i[1],
        Q_star_trs_prt_d_t_i_3 = Q_star_trs_prt_d_t_i[2],
        Q_star_trs_prt_d_t_i_4 = Q_star_trs_prt_d_t_i[3],
        Q_star_trs_prt_d_t_i_5 = Q_star_trs_prt_d_t_i[4]
    )

    # (10)　熱取得を含む負荷バランス時の冷房潜熱負荷
    L_star_CL_d_t_i = dc.get_L_star_CL_d_t_i(L_CS_d_t_i, L_CL_d_t_i, region)
    df_output = df_output.assign(
        L_star_CL_d_t_i_1 = L_star_CL_d_t_i[0],
        L_star_CL_d_t_i_2 = L_star_CL_d_t_i[1],
        L_star_CL_d_t_i_3 = L_star_CL_d_t_i[2],
        L_star_CL_d_t_i_4 = L_star_CL_d_t_i[3],
        L_star_CL_d_t_i_5 = L_star_CL_d_t_i[4]
    )

    if constants.carry_over_heat == 2:
        Theta_HBR_d_t_i = np.zeros((5, 24 * 365))
        Theta_NR_d_t = np.zeros((24 * 365))
        for hour in range(0, 24 * 365):
            # TODO: ここの中はまだ元のコードのコピペ。時刻別に分解する必要がある。

            # (9)　熱取得を含む負荷バランス時の冷房顕熱負荷
            L_star_CS_d_t_i = dc.get_L_star_CS_d_t_i(L_CS_d_t_i, Q_star_trs_prt_d_t_i, region)
            # (8)　熱損失を含む負荷バランス時の暖房負荷
            L_star_H_d_t_i = dc.get_L_star_H_d_t_i(L_H_d_t_i, Q_star_trs_prt_d_t_i, region)
            df_output = df_output.assign(
                L_star_H_d_t_i_1 = L_star_H_d_t_i[0],
                L_star_H_d_t_i_2 = L_star_H_d_t_i[1],
                L_star_H_d_t_i_3 = L_star_H_d_t_i[2],
                L_star_H_d_t_i_4 = L_star_H_d_t_i[3],
                L_star_H_d_t_i_5 = L_star_H_d_t_i[4]
            )

            ####################################################################################################################
            if type == PROCESS_TYPE_1 or type == PROCESS_TYPE_3:
                # (33)
                L_star_CL_d_t = dc.get_L_star_CL_d_t(L_star_CL_d_t_i)
                df_output['L_star_CL_d_t'] = L_star_CL_d_t

                # (32)
                L_star_CS_d_t = dc.get_L_star_CS_d_t(L_star_CS_d_t_i)
                df_output['L_star_CS_d_t'] = L_star_CL_d_t

                # (31)
                L_star_CL_max_d_t = dc.get_L_star_CL_max_d_t(L_star_CS_d_t)
                df_output['L_star_CL_d_t'] = L_star_CL_d_t

                # (30)
                L_star_dash_CL_d_t = dc.get_L_star_dash_CL_d_t(L_star_CL_max_d_t, L_star_CL_d_t)
                df_output['L_star_dash_CL_d_t'] = L_star_dash_CL_d_t

                # (29)
                L_star_dash_C_d_t = dc.get_L_star_dash_C_d_t(L_star_CS_d_t, L_star_dash_CL_d_t)
                df_output['L_star_dash_C_d_t'] = L_star_dash_C_d_t

                # (28)
                SHF_dash_d_t = dc.get_SHF_dash_d_t(L_star_CS_d_t, L_star_dash_C_d_t)
                df_output['SHF_dash_d_t'] = SHF_dash_d_t

                # (27)
                Q_hs_max_C_d_t = dc.get_Q_hs_max_C_d_t(type, q_hs_rtd_C, input_C_af_C)
                df_output['Q_hs_max_C_d_t'] = Q_hs_max_C_d_t

                # (26)
                Q_hs_max_CL_d_t = dc.get_Q_hs_max_CL_d_t(Q_hs_max_C_d_t, SHF_dash_d_t, L_star_dash_CL_d_t)
                df_output['Q_hs_max_CL_d_t'] = Q_hs_max_CL_d_t

                # (25)
                Q_hs_max_CS_d_t = dc.get_Q_hs_max_CS_d_t(Q_hs_max_C_d_t, SHF_dash_d_t)
                df_output['Q_hs_max_CS_d_t'] = Q_hs_max_CS_d_t

                # (24)
                C_df_H_d_t = dc.get_C_df_H_d_t(Theta_ex_d_t, h_ex_d_t)
                df_output['C_df_H_d_t'] = C_df_H_d_t

                # (23)
                Q_hs_max_H_d_t = dc.get_Q_hs_max_H_d_t(type, q_hs_rtd_H, C_df_H_d_t, input_C_af_H)
                df_output['Q_hs_max_H_d_t'] = Q_hs_max_H_d_t

            elif type == PROCESS_TYPE_2 or type == PROCESS_TYPE_4:
                # (24)　デフロストに関する暖房出力補正係数
                C_df_H_d_t = dc.get_C_df_H_d_t(Theta_ex_d_t, h_ex_d_t)
                df_output['C_df_H_d_t'] = C_df_H_d_t

                # 最大暖房能力比
                q_r_max_H = rac.get_q_r_max_H(q_max_H, q_rtd_H)
                df_output3['q_r_max_H'] = [q_r_max_H]

                # 最大暖房出力比
                Q_r_max_H_d_t = rac.calc_Q_r_max_H_d_t(q_rtd_C, q_r_max_H, Theta_ex_d_t)
                df_output['Q_r_max_H_d_t'] = Q_r_max_H_d_t

                # 最大暖房出力
                Q_max_H_d_t = rac.calc_Q_max_H_d_t(Q_r_max_H_d_t, q_rtd_H, Theta_ex_d_t, h_ex_d_t, input_C_af_H)
                Q_hs_max_H_d_t = Q_max_H_d_t
                df_output['Q_hs_max_H_d_t'] = Q_hs_max_H_d_t

                # 最大冷房能力比
                q_r_max_C = rac.get_q_r_max_C(q_max_C, q_rtd_C)
                df_output3['q_r_max_C'] = [q_r_max_C]

                # 最大冷房出力比
                Q_r_max_C_d_t = rac.calc_Q_r_max_C_d_t(q_r_max_C, q_rtd_C, Theta_ex_d_t)
                df_output['Q_r_max_C_d_t'] = Q_r_max_C_d_t

                # 最大冷房出力
                Q_max_C_d_t = rac.calc_Q_max_C_d_t(Q_r_max_C_d_t, q_rtd_C, input_C_af_C)
                Q_hs_max_C_d_t = Q_max_C_d_t
                df_output['Q_hs_max_C_d_t'] = Q_hs_max_C_d_t

                # 冷房負荷最小顕熱比
                SHF_L_min_c = rac.get_SHF_L_min_c()
                df_output3['SHF_L_min_c'] = [SHF_L_min_c]

                # 最大冷房潜熱負荷
                L_max_CL_d_t = rac.get_L_max_CL_d_t(np.sum(L_CS_d_t_i, axis=0), SHF_L_min_c)
                df_output['L_max_CL_d_t'] = L_max_CL_d_t

                # 補正冷房潜熱負荷
                L_dash_CL_d_t = rac.get_L_dash_CL_d_t(L_max_CL_d_t, np.sum(L_CL_d_t_i, axis=0))
                L_dash_C_d_t = rac.get_L_dash_C_d_t(np.sum(L_CS_d_t_i, axis=0), L_dash_CL_d_t)
                df_output['L_dash_CL_d_t'] = L_dash_CL_d_t
                df_output['L_dash_C_d_t'] = L_dash_C_d_t

                # 冷房負荷補正顕熱比
                SHF_dash_d_t = rac.get_SHF_dash_d_t(np.sum(L_CS_d_t_i, axis=0), L_dash_C_d_t)
                df_output['SHF_dash_d_t'] = SHF_dash_d_t

                # 最大冷房顕熱出力, 最大冷房潜熱出力
                Q_max_CS_d_t = rac.get_Q_max_CS_d_t(Q_max_C_d_t, SHF_dash_d_t)
                Q_max_CL_d_t = rac.get_Q_max_CL_d_t(Q_max_C_d_t, SHF_dash_d_t, L_dash_CL_d_t)
                Q_hs_max_C_d_t = Q_max_C_d_t
                Q_hs_max_CL_d_t = Q_max_CL_d_t
                Q_hs_max_CS_d_t = Q_max_CS_d_t
                df_output['Q_hs_max_C_d_t'] = Q_hs_max_C_d_t
                df_output['Q_hs_max_CL_d_t'] = Q_hs_max_CL_d_t
                df_output['Q_hs_max_CS_d_t'] = Q_hs_max_CS_d_t
            else:
                raise Exception('設備機器の種類の入力が不正です。')
            ####################################################################################################################

            # (20)　負荷バランス時の熱源機の入口における絶対湿度
            X_star_hs_in_d_t = dc.get_X_star_hs_in_d_t(X_star_NR_d_t)
            df_output['X_star_hs_in_d_t'] = X_star_hs_in_d_t

            # (19)　負荷バランス時の熱源機の入口における空気温度
            Theta_star_hs_in_d_t = dc.get_Theta_star_hs_in_d_t(Theta_star_NR_d_t)
            df_output['Theta_star_hs_in_d_t'] = Theta_star_hs_in_d_t

            # (18)　熱源機の出口における空気温度の最低値
            X_hs_out_min_C_d_t = dc.get_X_hs_out_min_C_d_t(X_star_hs_in_d_t, Q_hs_max_CL_d_t, V_dash_supply_d_t_i)
            df_output['X_hs_out_min_C_d_t'] = X_hs_out_min_C_d_t

            # (22)　熱源機の出口における要求絶対湿度
            X_req_d_t_i = dc.get_X_req_d_t_i(X_star_HBR_d_t, L_star_CL_d_t_i, V_dash_supply_d_t_i, region)
            df_output = df_output.assign(
                X_req_d_t_1 = X_req_d_t_i[0],
                X_req_d_t_2 = X_req_d_t_i[1],
                X_req_d_t_3 = X_req_d_t_i[2],
                X_req_d_t_4 = X_req_d_t_i[3],
                X_req_d_t_5 = X_req_d_t_i[4]
            )

            # (21)　熱源機の出口における要求空気温度
            Theta_req_d_t_i = dc.get_Theta_req_d_t_i(Theta_sur_d_t_i, Theta_star_HBR_d_t, V_dash_supply_d_t_i,
                                L_star_H_d_t_i, L_star_CS_d_t_i, l_duct_i, region)

            if underfloor_air_conditioning_air_supply:
                Theta_uf_d_t, Theta_g_surf_d_t = uf.calc_Theta(region, A_A, A_MR, A_OR, Q, YUCACO_r_A_ufvnt, underfloor_insulation, Theta_req_d_t_i[0], Theta_ex_d_t,
                                                        V_dash_supply_d_t_i[0], '', L_H_d_t_i, L_CS_d_t_i, R_g)
                df_output['Theta_req_d_t_1_bef'] = Theta_req_d_t_i[0]
                df_output['Theta_uf_d_t_1_req'] = Theta_uf_d_t
                if q_hs_rtd_H is not None:
                    Theta_req_d_t_i[0] = np.where(Theta_req_d_t_i[0] > Theta_uf_d_t, 
                                                  Theta_req_d_t_i[0] + (Theta_req_d_t_i[0] - Theta_uf_d_t),
                                                  Theta_req_d_t_i[0])
                else:
                    Theta_req_d_t_i[0] = np.where(Theta_req_d_t_i[0] < Theta_uf_d_t, 
                                                  Theta_req_d_t_i[0] + (Theta_req_d_t_i[0] - Theta_uf_d_t),
                                                  Theta_req_d_t_i[0])

                Theta_uf_d_t, Theta_g_surf_d_t = uf.calc_Theta(region, A_A, A_MR, A_OR, Q, YUCACO_r_A_ufvnt, underfloor_insulation, Theta_req_d_t_i[1], Theta_ex_d_t,
                                                        V_dash_supply_d_t_i[1], '', L_H_d_t_i, L_CS_d_t_i, R_g)
                df_output['Theta_req_d_t_2_bef'] = Theta_req_d_t_i[1]
                df_output['Theta_uf_d_t_2_req'] = Theta_uf_d_t
                if q_hs_rtd_H is not None:
                    Theta_req_d_t_i[1] = np.where(Theta_req_d_t_i[1] > Theta_uf_d_t, 
                                                  Theta_req_d_t_i[1] + (Theta_req_d_t_i[1] - Theta_uf_d_t),
                                                  Theta_req_d_t_i[1])
                else:
                    Theta_req_d_t_i[1] = np.where(Theta_req_d_t_i[1] < Theta_uf_d_t, 
                                                  Theta_req_d_t_i[1] + (Theta_req_d_t_i[1] - Theta_uf_d_t),
                                                  Theta_req_d_t_i[1])

            df_output = df_output.assign(
                Theta_req_d_t_1 = Theta_req_d_t_i[0],
                Theta_req_d_t_2 = Theta_req_d_t_i[1],
                Theta_req_d_t_3 = Theta_req_d_t_i[2],
                Theta_req_d_t_4 = Theta_req_d_t_i[3],
                Theta_req_d_t_5 = Theta_req_d_t_i[4]
            )

            # (15)　熱源機の出口における絶対湿度
            X_hs_out_d_t = dc.get_X_hs_out_d_t(X_NR_d_t, X_req_d_t_i, V_dash_supply_d_t_i, X_hs_out_min_C_d_t, L_star_CL_d_t_i, region)
            df_output['X_hs_out_d_t'] = X_hs_out_d_t

            # 式(14)(46)(48)の条件に合わせてTheta_NR_d_tを初期化
            Theta_NR_d_t = np.zeros(24 * 365)

            # (17)　冷房時の熱源機の出口における空気温度の最低値
            Theta_hs_out_min_C_d_t = dc.get_Theta_hs_out_min_C_d_t(Theta_star_hs_in_d_t, Q_hs_max_CS_d_t, V_dash_supply_d_t_i)
            df_output['Theta_hs_out_min_C_d_t'] = Theta_hs_out_min_C_d_t

            # (16)　暖房時の熱源機の出口における空気温度の最高値
            Theta_hs_out_max_H_d_t = dc.get_Theta_hs_out_max_H_d_t(Theta_star_hs_in_d_t, Q_hs_max_H_d_t, V_dash_supply_d_t_i)
            df_output['Theta_hs_out_max_H_d_t'] = Theta_hs_out_max_H_d_t

            # L_star_H_d_t_i，L_star_CS_d_t_iの暖冷房区画1～5を合算し0以上だった場合の順序で計算
            # (14)　熱源機の出口における空気温度
            Theta_hs_out_d_t = dc.get_Theta_hs_out_d_t(VAV, Theta_req_d_t_i, V_dash_supply_d_t_i,
                                                    L_star_H_d_t_i, L_star_CS_d_t_i, region, Theta_NR_d_t,
                                                    Theta_hs_out_max_H_d_t, Theta_hs_out_min_C_d_t)
            df_output['Theta_hs_out_d_t'] = Theta_hs_out_d_t

            # (43)　暖冷房区画𝑖の吹き出し風量
            V_supply_d_t_i = dc.get_V_supply_d_t_i(L_star_H_d_t_i, L_star_CS_d_t_i, Theta_sur_d_t_i, l_duct_i, Theta_star_HBR_d_t,
                                                            V_vent_g_i, V_dash_supply_d_t_i, VAV, region, Theta_hs_out_d_t)

            df_output = df_output.assign(
                V_supply_d_t_1 = V_supply_d_t_i[0],
                V_supply_d_t_2 = V_supply_d_t_i[1],
                V_supply_d_t_3 = V_supply_d_t_i[2],
                V_supply_d_t_4 = V_supply_d_t_i[3],
                V_supply_d_t_5 = V_supply_d_t_i[4]
            )

            # (41)　暖冷房区画𝑖の吹き出し温度
            Theta_supply_d_t_i = dc.get_Thata_supply_d_t_i(Theta_sur_d_t_i, Theta_hs_out_d_t, Theta_star_HBR_d_t, l_duct_i,
                                                           V_supply_d_t_i, L_star_H_d_t_i, L_star_CS_d_t_i, region)
            if underfloor_air_conditioning_air_supply:
                Theta_uf_d_t, Theta_g_surf_d_t = uf.calc_Theta(region, A_A, A_MR, A_OR, Q, YUCACO_r_A_ufvnt, underfloor_insulation, Theta_supply_d_t_i[0], Theta_ex_d_t,
                                                        V_dash_supply_d_t_i[0], '', L_H_d_t_i, L_CS_d_t_i, R_g)
                df_output['Theta_supply_d_t_1_bef'] = Theta_supply_d_t_i[0]
                df_output['Theta_uf_d_t_1_sup'] = Theta_uf_d_t
                if q_hs_rtd_H is not None:
                    Theta_supply_d_t_i[0] = np.where(Theta_supply_d_t_i[0] > Theta_uf_d_t, 
                                                     Theta_uf_d_t,
                                                     Theta_supply_d_t_i[0])
                elif q_hs_rtd_C is not None:
                    Theta_supply_d_t_i[0] = np.where(Theta_supply_d_t_i[0] < Theta_uf_d_t, 
                                                     Theta_uf_d_t,
                                                     Theta_supply_d_t_i[0])

                Theta_uf_d_t, Theta_g_surf_d_t = uf.calc_Theta(region, A_A, A_MR, A_OR, Q, YUCACO_r_A_ufvnt, underfloor_insulation, Theta_supply_d_t_i[1], Theta_ex_d_t,
                                                        V_dash_supply_d_t_i[1], '', L_H_d_t_i, L_CS_d_t_i, R_g)
                df_output['Theta_supply_d_t_2_bef'] = Theta_supply_d_t_i[1]
                df_output['Theta_uf_d_t_2_sup'] = Theta_uf_d_t
                if q_hs_rtd_H is not None:
                    Theta_supply_d_t_i[1] = np.where(Theta_supply_d_t_i[1] > Theta_uf_d_t, 
                                                     Theta_uf_d_t,
                                                     Theta_supply_d_t_i[1])
                elif q_hs_rtd_C is not None:
                    Theta_supply_d_t_i[1] = np.where(Theta_supply_d_t_i[1] < Theta_uf_d_t, 
                                                     Theta_uf_d_t,
                                                     Theta_supply_d_t_i[1])

            df_output = df_output.assign(
                Theta_supply_d_t_1 = Theta_supply_d_t_i[0],
                Theta_supply_d_t_2 = Theta_supply_d_t_i[1],
                Theta_supply_d_t_3 = Theta_supply_d_t_i[2],
                Theta_supply_d_t_4 = Theta_supply_d_t_i[3],
                Theta_supply_d_t_5 = Theta_supply_d_t_i[4]
            )

            # (46)　暖冷房区画𝑖の実際の居室の室温
            Theta_HBR_d_t_i[:, hour] = dc.get_Theta_HBR_d_t_i_2023(Theta_star_HBR_d_t, V_supply_d_t_i, Theta_supply_d_t_i, U_prt, A_prt_i, Q,
                                                          A_HCZ_i, L_star_H_d_t_i, L_star_CS_d_t_i, region, hour)

            # (48)　実際の非居室の室温
            Theta_NR_d_t[hour] = dc.get_Theta_NR_d_t_2023(Theta_star_NR_d_t, Theta_star_HBR_d_t, Theta_HBR_d_t_i, A_NR, V_vent_l_NR_d_t,
                                                V_dash_supply_d_t_i, V_supply_d_t_i, U_prt, A_prt_i, Q, hour)

    else:
        # (9)　熱取得を含む負荷バランス時の冷房顕熱負荷
        L_star_CS_d_t_i = dc.get_L_star_CS_d_t_i(L_CS_d_t_i, Q_star_trs_prt_d_t_i, region)
        df_output = df_output.assign(
            L_star_CS_d_t_i_1 = L_star_CS_d_t_i[0],
            L_star_CS_d_t_i_2 = L_star_CS_d_t_i[1],
            L_star_CS_d_t_i_3 = L_star_CS_d_t_i[2],
            L_star_CS_d_t_i_4 = L_star_CS_d_t_i[3],
            L_star_CS_d_t_i_5 = L_star_CS_d_t_i[4]
        )

        # (8)　熱損失を含む負荷バランス時の暖房負荷
        L_star_H_d_t_i = dc.get_L_star_H_d_t_i(L_H_d_t_i, Q_star_trs_prt_d_t_i, region)
        df_output = df_output.assign(
            L_star_H_d_t_i_1 = L_star_H_d_t_i[0],
            L_star_H_d_t_i_2 = L_star_H_d_t_i[1],
            L_star_H_d_t_i_3 = L_star_H_d_t_i[2],
            L_star_H_d_t_i_4 = L_star_H_d_t_i[3],
            L_star_H_d_t_i_5 = L_star_H_d_t_i[4]
        )

        ####################################################################################################################
        if type == PROCESS_TYPE_1 or type == PROCESS_TYPE_3:
            # (33)
            L_star_CL_d_t = dc.get_L_star_CL_d_t(L_star_CL_d_t_i)
            df_output['L_star_CL_d_t'] = L_star_CL_d_t

            # (32)
            L_star_CS_d_t = dc.get_L_star_CS_d_t(L_star_CS_d_t_i)
            df_output['L_star_CS_d_t'] = L_star_CL_d_t

            # (31)
            L_star_CL_max_d_t = dc.get_L_star_CL_max_d_t(L_star_CS_d_t)
            df_output['L_star_CL_d_t'] = L_star_CL_d_t

            # (30)
            L_star_dash_CL_d_t = dc.get_L_star_dash_CL_d_t(L_star_CL_max_d_t, L_star_CL_d_t)
            df_output['L_star_dash_CL_d_t'] = L_star_dash_CL_d_t

            # (29)
            L_star_dash_C_d_t = dc.get_L_star_dash_C_d_t(L_star_CS_d_t, L_star_dash_CL_d_t)
            df_output['L_star_dash_C_d_t'] = L_star_dash_C_d_t

            # (28)
            SHF_dash_d_t = dc.get_SHF_dash_d_t(L_star_CS_d_t, L_star_dash_C_d_t)
            df_output['SHF_dash_d_t'] = SHF_dash_d_t

            # (27)
            Q_hs_max_C_d_t = dc.get_Q_hs_max_C_d_t(type, q_hs_rtd_C, input_C_af_C)
            df_output['Q_hs_max_C_d_t'] = Q_hs_max_C_d_t

            # (26)
            Q_hs_max_CL_d_t = dc.get_Q_hs_max_CL_d_t(Q_hs_max_C_d_t, SHF_dash_d_t, L_star_dash_CL_d_t)
            df_output['Q_hs_max_CL_d_t'] = Q_hs_max_CL_d_t

            # (25)
            Q_hs_max_CS_d_t = dc.get_Q_hs_max_CS_d_t(Q_hs_max_C_d_t, SHF_dash_d_t)
            df_output['Q_hs_max_CS_d_t'] = Q_hs_max_CS_d_t

            # (24)
            C_df_H_d_t = dc.get_C_df_H_d_t(Theta_ex_d_t, h_ex_d_t)
            df_output['C_df_H_d_t'] = C_df_H_d_t

            # (23)
            Q_hs_max_H_d_t = dc.get_Q_hs_max_H_d_t(type, q_hs_rtd_H, C_df_H_d_t, input_C_af_H)
            df_output['Q_hs_max_H_d_t'] = Q_hs_max_H_d_t

        elif type == PROCESS_TYPE_2 or type == PROCESS_TYPE_4:
            # (24)　デフロストに関する暖房出力補正係数
            C_df_H_d_t = dc.get_C_df_H_d_t(Theta_ex_d_t, h_ex_d_t)
            df_output['C_df_H_d_t'] = C_df_H_d_t

            # 最大暖房能力比
            q_r_max_H = rac.get_q_r_max_H(q_max_H, q_rtd_H)
            df_output3['q_r_max_H'] = [q_r_max_H]

            # 最大暖房出力比
            Q_r_max_H_d_t = rac.calc_Q_r_max_H_d_t(q_rtd_C, q_r_max_H, Theta_ex_d_t)
            df_output['Q_r_max_H_d_t'] = Q_r_max_H_d_t

            # 最大暖房出力
            Q_max_H_d_t = rac.calc_Q_max_H_d_t(Q_r_max_H_d_t, q_rtd_H, Theta_ex_d_t, h_ex_d_t, input_C_af_H)
            Q_hs_max_H_d_t = Q_max_H_d_t
            df_output['Q_hs_max_H_d_t'] = Q_hs_max_H_d_t

            # 最大冷房能力比
            q_r_max_C = rac.get_q_r_max_C(q_max_C, q_rtd_C)
            df_output3['q_r_max_C'] = [q_r_max_C]

            # 最大冷房出力比
            Q_r_max_C_d_t = rac.calc_Q_r_max_C_d_t(q_r_max_C, q_rtd_C, Theta_ex_d_t)
            df_output['Q_r_max_C_d_t'] = Q_r_max_C_d_t

            # 最大冷房出力
            Q_max_C_d_t = rac.calc_Q_max_C_d_t(Q_r_max_C_d_t, q_rtd_C, input_C_af_C)
            Q_hs_max_C_d_t = Q_max_C_d_t
            df_output['Q_hs_max_C_d_t'] = Q_hs_max_C_d_t

            # 冷房負荷最小顕熱比
            SHF_L_min_c = rac.get_SHF_L_min_c()
            df_output3['SHF_L_min_c'] = [SHF_L_min_c]

            # 最大冷房潜熱負荷
            L_max_CL_d_t = rac.get_L_max_CL_d_t(np.sum(L_CS_d_t_i, axis=0), SHF_L_min_c)
            df_output['L_max_CL_d_t'] = L_max_CL_d_t

            # 補正冷房潜熱負荷
            L_dash_CL_d_t = rac.get_L_dash_CL_d_t(L_max_CL_d_t, np.sum(L_CL_d_t_i, axis=0))
            L_dash_C_d_t = rac.get_L_dash_C_d_t(np.sum(L_CS_d_t_i, axis=0), L_dash_CL_d_t)
            df_output['L_dash_CL_d_t'] = L_dash_CL_d_t
            df_output['L_dash_C_d_t'] = L_dash_C_d_t

            # 冷房負荷補正顕熱比
            SHF_dash_d_t = rac.get_SHF_dash_d_t(np.sum(L_CS_d_t_i, axis=0), L_dash_C_d_t)
            df_output['SHF_dash_d_t'] = SHF_dash_d_t

            # 最大冷房顕熱出力, 最大冷房潜熱出力
            Q_max_CS_d_t = rac.get_Q_max_CS_d_t(Q_max_C_d_t, SHF_dash_d_t)
            Q_max_CL_d_t = rac.get_Q_max_CL_d_t(Q_max_C_d_t, SHF_dash_d_t, L_dash_CL_d_t)
            Q_hs_max_C_d_t = Q_max_C_d_t
            Q_hs_max_CL_d_t = Q_max_CL_d_t
            Q_hs_max_CS_d_t = Q_max_CS_d_t
            df_output['Q_hs_max_C_d_t'] = Q_hs_max_C_d_t
            df_output['Q_hs_max_CL_d_t'] = Q_hs_max_CL_d_t
            df_output['Q_hs_max_CS_d_t'] = Q_hs_max_CS_d_t
        else:
            raise Exception('設備機器の種類の入力が不正です。')
        ####################################################################################################################

        # (20)　負荷バランス時の熱源機の入口における絶対湿度
        X_star_hs_in_d_t = dc.get_X_star_hs_in_d_t(X_star_NR_d_t)
        df_output['X_star_hs_in_d_t'] = X_star_hs_in_d_t

        # (19)　負荷バランス時の熱源機の入口における空気温度
        Theta_star_hs_in_d_t = dc.get_Theta_star_hs_in_d_t(Theta_star_NR_d_t)
        df_output['Theta_star_hs_in_d_t'] = Theta_star_hs_in_d_t

        # (18)　熱源機の出口における空気温度の最低値
        X_hs_out_min_C_d_t = dc.get_X_hs_out_min_C_d_t(X_star_hs_in_d_t, Q_hs_max_CL_d_t, V_dash_supply_d_t_i)
        df_output['X_hs_out_min_C_d_t'] = X_hs_out_min_C_d_t

        # (22)　熱源機の出口における要求絶対湿度
        X_req_d_t_i = dc.get_X_req_d_t_i(X_star_HBR_d_t, L_star_CL_d_t_i, V_dash_supply_d_t_i, region)
        df_output = df_output.assign(
            X_req_d_t_1 = X_req_d_t_i[0],
            X_req_d_t_2 = X_req_d_t_i[1],
            X_req_d_t_3 = X_req_d_t_i[2],
            X_req_d_t_4 = X_req_d_t_i[3],
            X_req_d_t_5 = X_req_d_t_i[4]
        )

        # (21)　熱源機の出口における要求空気温度
        Theta_req_d_t_i = dc.get_Theta_req_d_t_i(Theta_sur_d_t_i, Theta_star_HBR_d_t, V_dash_supply_d_t_i,
                            L_star_H_d_t_i, L_star_CS_d_t_i, l_duct_i, region)

        if underfloor_air_conditioning_air_supply:
            Theta_uf_d_t, Theta_g_surf_d_t = uf.calc_Theta(region, A_A, A_MR, A_OR, Q, YUCACO_r_A_ufvnt, underfloor_insulation, Theta_req_d_t_i[0], Theta_ex_d_t,
                                                    V_dash_supply_d_t_i[0], '', L_H_d_t_i, L_CS_d_t_i, R_g)
            df_output['Theta_req_d_t_1_bef'] = Theta_req_d_t_i[0]
            df_output['Theta_uf_d_t_1_req'] = Theta_uf_d_t
            if q_hs_rtd_H is not None:
                Theta_req_d_t_i[0] = np.where(Theta_req_d_t_i[0] > Theta_uf_d_t, 
                                              Theta_req_d_t_i[0] + (Theta_req_d_t_i[0] - Theta_uf_d_t),
                                              Theta_req_d_t_i[0])
            else:
                Theta_req_d_t_i[0] = np.where(Theta_req_d_t_i[0] < Theta_uf_d_t, 
                                              Theta_req_d_t_i[0] + (Theta_req_d_t_i[0] - Theta_uf_d_t),
                                              Theta_req_d_t_i[0])

            Theta_uf_d_t, Theta_g_surf_d_t = uf.calc_Theta(region, A_A, A_MR, A_OR, Q, YUCACO_r_A_ufvnt, underfloor_insulation, Theta_req_d_t_i[1], Theta_ex_d_t,
                                                    V_dash_supply_d_t_i[1], '', L_H_d_t_i, L_CS_d_t_i, R_g)
            df_output['Theta_req_d_t_2_bef'] = Theta_req_d_t_i[1]
            df_output['Theta_uf_d_t_2_req'] = Theta_uf_d_t
            if q_hs_rtd_H is not None:
                Theta_req_d_t_i[1] = np.where(Theta_req_d_t_i[1] > Theta_uf_d_t, 
                                              Theta_req_d_t_i[1] + (Theta_req_d_t_i[1] - Theta_uf_d_t),
                                              Theta_req_d_t_i[1])
            else:
                Theta_req_d_t_i[1] = np.where(Theta_req_d_t_i[1] < Theta_uf_d_t, 
                                              Theta_req_d_t_i[1] + (Theta_req_d_t_i[1] - Theta_uf_d_t),
                                              Theta_req_d_t_i[1])

        df_output = df_output.assign(
            Theta_req_d_t_1 = Theta_req_d_t_i[0],
            Theta_req_d_t_2 = Theta_req_d_t_i[1],
            Theta_req_d_t_3 = Theta_req_d_t_i[2],
            Theta_req_d_t_4 = Theta_req_d_t_i[3],
            Theta_req_d_t_5 = Theta_req_d_t_i[4]
        )

        # (15)　熱源機の出口における絶対湿度
        X_hs_out_d_t = dc.get_X_hs_out_d_t(X_NR_d_t, X_req_d_t_i, V_dash_supply_d_t_i, X_hs_out_min_C_d_t, L_star_CL_d_t_i, region)
        df_output['X_hs_out_d_t'] = X_hs_out_d_t

        # 式(14)(46)(48)の条件に合わせてTheta_NR_d_tを初期化
        Theta_NR_d_t = np.zeros(24 * 365)

        # (17)　冷房時の熱源機の出口における空気温度の最低値
        Theta_hs_out_min_C_d_t = dc.get_Theta_hs_out_min_C_d_t(Theta_star_hs_in_d_t, Q_hs_max_CS_d_t, V_dash_supply_d_t_i)
        df_output['Theta_hs_out_min_C_d_t'] = Theta_hs_out_min_C_d_t

        # (16)　暖房時の熱源機の出口における空気温度の最高値
        Theta_hs_out_max_H_d_t = dc.get_Theta_hs_out_max_H_d_t(Theta_star_hs_in_d_t, Q_hs_max_H_d_t, V_dash_supply_d_t_i)
        df_output['Theta_hs_out_max_H_d_t'] = Theta_hs_out_max_H_d_t

        # L_star_H_d_t_i，L_star_CS_d_t_iの暖冷房区画1～5を合算し0以上だった場合の順序で計算
        # (14)　熱源機の出口における空気温度
        Theta_hs_out_d_t = dc.get_Theta_hs_out_d_t(VAV, Theta_req_d_t_i, V_dash_supply_d_t_i,
                                                L_star_H_d_t_i, L_star_CS_d_t_i, region, Theta_NR_d_t,
                                                Theta_hs_out_max_H_d_t, Theta_hs_out_min_C_d_t)
        df_output['Theta_hs_out_d_t'] = Theta_hs_out_d_t

        # (43)　暖冷房区画𝑖の吹き出し風量
        V_supply_d_t_i = dc.get_V_supply_d_t_i(L_star_H_d_t_i, L_star_CS_d_t_i, Theta_sur_d_t_i, l_duct_i, Theta_star_HBR_d_t,
                                                        V_vent_g_i, V_dash_supply_d_t_i, VAV, region, Theta_hs_out_d_t)

        df_output = df_output.assign(
            V_supply_d_t_1 = V_supply_d_t_i[0],
            V_supply_d_t_2 = V_supply_d_t_i[1],
            V_supply_d_t_3 = V_supply_d_t_i[2],
            V_supply_d_t_4 = V_supply_d_t_i[3],
            V_supply_d_t_5 = V_supply_d_t_i[4]
        )

        # (41)　暖冷房区画𝑖の吹き出し温度
        Theta_supply_d_t_i = dc.get_Thata_supply_d_t_i(Theta_sur_d_t_i, Theta_hs_out_d_t, Theta_star_HBR_d_t, l_duct_i,
                                                       V_supply_d_t_i, L_star_H_d_t_i, L_star_CS_d_t_i, region)
        if underfloor_air_conditioning_air_supply:
            Theta_uf_d_t, Theta_g_surf_d_t = uf.calc_Theta(region, A_A, A_MR, A_OR, Q, YUCACO_r_A_ufvnt, underfloor_insulation, Theta_supply_d_t_i[0], Theta_ex_d_t,
                                                    V_dash_supply_d_t_i[0], '', L_H_d_t_i, L_CS_d_t_i, R_g)
            df_output['Theta_supply_d_t_1_bef'] = Theta_supply_d_t_i[0]
            df_output['Theta_uf_d_t_1_sup'] = Theta_uf_d_t
            if q_hs_rtd_H is not None:
                Theta_supply_d_t_i[0] = np.where(Theta_supply_d_t_i[0] > Theta_uf_d_t, 
                                                 Theta_uf_d_t,
                                                 Theta_supply_d_t_i[0])
            elif q_hs_rtd_C is not None:
                Theta_supply_d_t_i[0] = np.where(Theta_supply_d_t_i[0] < Theta_uf_d_t, 
                                                 Theta_uf_d_t,
                                                 Theta_supply_d_t_i[0])

            Theta_uf_d_t, Theta_g_surf_d_t = uf.calc_Theta(region, A_A, A_MR, A_OR, Q, YUCACO_r_A_ufvnt, underfloor_insulation, Theta_supply_d_t_i[1], Theta_ex_d_t,
                                                    V_dash_supply_d_t_i[1], '', L_H_d_t_i, L_CS_d_t_i, R_g)
            df_output['Theta_supply_d_t_2_bef'] = Theta_supply_d_t_i[1]
            df_output['Theta_uf_d_t_2_sup'] = Theta_uf_d_t
            if q_hs_rtd_H is not None:
                Theta_supply_d_t_i[1] = np.where(Theta_supply_d_t_i[1] > Theta_uf_d_t, 
                                                 Theta_uf_d_t,
                                                 Theta_supply_d_t_i[1])
            elif q_hs_rtd_C is not None:
                Theta_supply_d_t_i[1] = np.where(Theta_supply_d_t_i[1] < Theta_uf_d_t, 
                                                 Theta_uf_d_t,
                                                 Theta_supply_d_t_i[1])

        df_output = df_output.assign(
            Theta_supply_d_t_1 = Theta_supply_d_t_i[0],
            Theta_supply_d_t_2 = Theta_supply_d_t_i[1],
            Theta_supply_d_t_3 = Theta_supply_d_t_i[2],
            Theta_supply_d_t_4 = Theta_supply_d_t_i[3],
            Theta_supply_d_t_5 = Theta_supply_d_t_i[4]
        )

        # (46)　暖冷房区画𝑖の実際の居室の室温
        Theta_HBR_d_t_i = dc.get_Theta_HBR_d_t_i(Theta_star_HBR_d_t, V_supply_d_t_i, Theta_supply_d_t_i, U_prt, A_prt_i, Q,
                                                 A_HCZ_i, L_star_H_d_t_i, L_star_CS_d_t_i, region)

        # (48)　実際の非居室の室温
        Theta_NR_d_t = dc.get_Theta_NR_d_t(Theta_star_NR_d_t, Theta_star_HBR_d_t, Theta_HBR_d_t_i, A_NR, V_vent_l_NR_d_t,
                                            V_dash_supply_d_t_i, V_supply_d_t_i, U_prt, A_prt_i, Q)

    df_output = df_output.assign(
        Theta_HBR_d_t_1 = Theta_HBR_d_t_i[0],
        Theta_HBR_d_t_2 = Theta_HBR_d_t_i[1],
        Theta_HBR_d_t_3 = Theta_HBR_d_t_i[2],
        Theta_HBR_d_t_4 = Theta_HBR_d_t_i[3],
        Theta_HBR_d_t_5 = Theta_HBR_d_t_i[4],
        Theta_NR_d_t = Theta_NR_d_t
    )

    # L_star_H_d_t_i，L_star_CS_d_t_iの暖冷房区画1～5を合算し0以下だった場合の為に再計算
    # (14)　熱源機の出口における空気温度
    Theta_hs_out_d_t = dc.get_Theta_hs_out_d_t(VAV, Theta_req_d_t_i, V_dash_supply_d_t_i,
                                            L_star_H_d_t_i, L_star_CS_d_t_i, region, Theta_NR_d_t,
                                            Theta_hs_out_max_H_d_t, Theta_hs_out_min_C_d_t)
    df_output['Theta_hs_out_d_t'] = Theta_hs_out_d_t

    # (42)　暖冷房区画𝑖の吹き出し絶対湿度
    X_supply_d_t_i = dc.get_X_supply_d_t_i(X_star_HBR_d_t, X_hs_out_d_t, L_star_CL_d_t_i, region)
    df_output = df_output.assign(
        X_supply_d_t_1 = X_supply_d_t_i[0],
        X_supply_d_t_2 = X_supply_d_t_i[1],
        X_supply_d_t_3 = X_supply_d_t_i[2],
        X_supply_d_t_4 = X_supply_d_t_i[3],
        X_supply_d_t_5 = X_supply_d_t_i[4]
    )

    # (35)　熱源機の風量のうちの全般換気分
    V_hs_vent_d_t = dc.get_V_hs_vent_d_t(V_vent_g_i, general_ventilation)
    df_output['V_hs_vent_d_t'] = V_hs_vent_d_t 

    # (34)　熱源機の風量
    V_hs_supply_d_t = dc.get_V_hs_supply_d_t(V_supply_d_t_i)
    df_output['V_hs_supply_d_t'] = V_hs_supply_d_t

    # (13)　熱源機の入口における絶対湿度
    X_hs_in_d_t = dc.get_X_hs_in_d_t(X_NR_d_t)
    df_output['X_hs_in_d_t'] = X_hs_in_d_t

    # (12)　熱源機の入口における空気温度
    Theta_hs_in_d_t = dc.get_Theta_hs_in_d_t(Theta_NR_d_t)
    df_output['Theta_hs_in_d_t'] = Theta_hs_in_d_t  

    # (7)　間仕切りの熱取得を含む実際の冷房潜熱負荷
    L_dash_CL_d_t_i = dc.get_L_dash_CL_d_t_i(V_supply_d_t_i, X_HBR_d_t_i, X_supply_d_t_i, region)
    df_output = df_output.assign(
        L_dash_CL_d_t_1 = L_dash_CL_d_t_i[0],
        L_dash_CL_d_t_2 = L_dash_CL_d_t_i[1],
        L_dash_CL_d_t_3 = L_dash_CL_d_t_i[2],
        L_dash_CL_d_t_4 = L_dash_CL_d_t_i[3],
        L_dash_CL_d_t_5 = L_dash_CL_d_t_i[4]
    )

    # (6)　間仕切りの熱取得を含む実際の冷房顕熱負荷
    L_dash_CS_d_t_i = dc.get_L_dash_CS_d_t_i(V_supply_d_t_i, Theta_supply_d_t_i, Theta_HBR_d_t_i, region)
    df_output = df_output.assign(
        L_dash_CS_d_t_1 = L_dash_CS_d_t_i[0],
        L_dash_CS_d_t_2 = L_dash_CS_d_t_i[1],
        L_dash_CS_d_t_3 = L_dash_CS_d_t_i[2],
        L_dash_CS_d_t_4 = L_dash_CS_d_t_i[3],
        L_dash_CS_d_t_5 = L_dash_CS_d_t_i[4]
    )

    # (5)　間仕切りの熱損失を含む実際の暖房負荷
    L_dash_H_d_t_i = dc.get_L_dash_H_d_t_i(V_supply_d_t_i, Theta_supply_d_t_i, Theta_HBR_d_t_i, region)
    df_output = df_output.assign(
        L_dash_H_d_t_1 = L_dash_H_d_t_i[0],
        L_dash_H_d_t_2 = L_dash_H_d_t_i[1],
        L_dash_H_d_t_3 = L_dash_H_d_t_i[2],
        L_dash_H_d_t_4 = L_dash_H_d_t_i[3],
        L_dash_H_d_t_5 = L_dash_H_d_t_i[4]
    )

    # (4)　冷房設備機器の未処理冷房潜熱負荷
    Q_UT_CL_d_t_i = dc.get_Q_UT_CL_d_t_i(L_star_CL_d_t_i, L_dash_CL_d_t_i)
    df_output = df_output.assign(
        Q_UT_CL_d_t_1 = Q_UT_CL_d_t_i[0],
        Q_UT_CL_d_t_2 = Q_UT_CL_d_t_i[1],
        Q_UT_CL_d_t_3 = Q_UT_CL_d_t_i[2],
        Q_UT_CL_d_t_4 = Q_UT_CL_d_t_i[3],
        Q_UT_CL_d_t_5 = Q_UT_CL_d_t_i[4]
    )

    # (3)　冷房設備機器の未処理冷房顕熱負荷
    Q_UT_CS_d_t_i = dc.get_Q_UT_CS_d_t_i(L_star_CS_d_t_i, L_dash_CS_d_t_i)
    df_output = df_output.assign(
        Q_UT_CS_d_t_1 = Q_UT_CS_d_t_i[0],
        Q_UT_CS_d_t_2 = Q_UT_CS_d_t_i[1],
        Q_UT_CS_d_t_3 = Q_UT_CS_d_t_i[2],
        Q_UT_CS_d_t_4 = Q_UT_CS_d_t_i[3],
        Q_UT_CS_d_t_5 = Q_UT_CS_d_t_i[4]
    )

    # (2)　暖房設備機器等の未処理暖房負荷
    Q_UT_H_d_t_i = dc.get_Q_UT_H_d_t_i(L_star_H_d_t_i, L_dash_H_d_t_i)
    df_output = df_output.assign(
        Q_UT_H_d_t_1 = Q_UT_H_d_t_i[0],
        Q_UT_H_d_t_2 = Q_UT_H_d_t_i[1],
        Q_UT_H_d_t_3 = Q_UT_H_d_t_i[2],
        Q_UT_H_d_t_4 = Q_UT_H_d_t_i[3],
        Q_UT_H_d_t_5 = Q_UT_H_d_t_i[4]
    )

    # (1)　冷房設備の未処理冷房負荷の設計一次エネルギー消費量相当値
    E_C_UT_d_t = dc.get_E_C_UT_d_t(Q_UT_CL_d_t_i, Q_UT_CS_d_t_i, region)
    df_output['E_C_UT_d_t'] = E_C_UT_d_t

    if q_hs_rtd_H is not None:
        df_output3.to_csv(case_name + version_info() + '_H_output3.csv', encoding = 'cp932')
        df_output2.to_csv(case_name + version_info() + '_H_output4.csv', encoding = 'cp932')
        df_output.to_csv(case_name  + version_info() + '_H_output5.csv', encoding = 'cp932')
    else:
        df_output3.to_csv(case_name + version_info() + '_C_output3.csv', encoding = 'cp932')
        df_output2.to_csv(case_name + version_info() + '_C_output4.csv', encoding = 'cp932')
        df_output.to_csv(case_name  + version_info() + '_C_output5.csv', encoding = 'cp932')

    return E_C_UT_d_t, Q_UT_H_d_t_i, Q_UT_CS_d_t_i, Q_UT_CL_d_t_i, Theta_hs_out_d_t, Theta_hs_in_d_t, Theta_ex_d_t, \
           X_hs_out_d_t, X_hs_in_d_t, V_hs_supply_d_t, V_hs_vent_d_t, C_df_H_d_t

def calc_E_E_H_d_t(
        case_name,
        Theta_hs_out_d_t, Theta_hs_in_d_t, Theta_ex_d_t,  # 空気温度
        V_hs_supply_d_t, V_hs_vent_d_t, V_hs_dsgn_H,      # 風量
        C_df_H_d_t,                                       # 暖房出力補正係数
        q_hs_min_H,                                       # 最小暖房時
        q_hs_mid_H, P_hs_mid_H, V_fan_mid_H, P_fan_mid_H,  # 中間暖房時
        q_max_C, q_max_H,                                  # 最大暖房時
        q_rtd_C, q_hs_rtd_C,                               # 定格冷房時
        q_rtd_H, e_rtd_H, P_rac_fan_rtd_H, V_fan_rtd_H, P_fan_rtd_H, q_hs_rtd_H, P_hs_rtd_H,  # 定格暖房時
        type, region, dualcompressor_H, EquipmentSpec, input_C_af_H, f_SFP_H, climateFile,  # その他
        simu_R_H=None, spec: Spec=None, Theta_real_inner=None, RH_real_inner=None):  # 電中研モデルのみ使用
    """ (1)
    Args:
        P_fan_rad_H: 定格暖房能力試験 室内側送風機の消費電力 [W]\n
        日付dの時刻tにおける\n
            V_hs_vent_d_t:   熱源機の風量のうちの全般換気分 [m3/h]\n
            V_hs_supply_d_t: 熱源機の風量 [m3/h]\n
            X_hs_in_d_t:     熱源機の入口における絶対湿度 [kg/kg(DA)]\n
    Returns:
        日付dの時刻tにおける\n
            E_E_H_d_t:     1時間当たりの暖房時の消費電力量[kWh/h]
            E_E_fan_H_d_t: 1時間当たりの暖房時消費電力量の送風機による付加分[kWh/h]
            q_hs_H_d_t:    1時間当たりの熱源機の平均暖房能力[W]
    """
    # (3) 日付dの時刻tにおける1時間当たりの熱源機の平均暖房能力(W)
    q_hs_H_d_t = dc_a.get_q_hs_H_d_t(Theta_hs_out_d_t, Theta_hs_in_d_t, V_hs_supply_d_t, C_df_H_d_t, region)

    _logger.NDdebug("V_hs_supply_d_t", V_hs_supply_d_t)

    if type == PROCESS_TYPE_1 or type == PROCESS_TYPE_3:

        """ e_th: ヒートポンプサイクルの理論効率(-) """

        # (20) 中間暖房能力運転時
        e_th_mid_H = dc_a.calc_e_th_mid_H(type, V_fan_mid_H, q_hs_mid_H, q_hs_rtd_C)
        # (19) 定格暖房能力運転時
        e_th_rtd_H = dc_a.calc_e_th_rtd_H(type, V_fan_rtd_H, q_hs_rtd_H, q_hs_rtd_C)
        # (17) 日付dの時刻tにおける暖房時
        e_th_H_d_t = dc_a.calc_e_th_H_d_t(type, Theta_ex_d_t, Theta_hs_in_d_t, Theta_hs_out_d_t, V_hs_supply_d_t, q_hs_rtd_C)

        """ e_r: ヒートポンプサイクルの理論効率に対する熱源機の効率の比(-) """

        if type == PROCESS_TYPE_3:  #コンプレッサ効率特性
            # 日付dの時刻tにおける暖房時
            e_r_H_d_t = dc_a.get_e_r_H_d_t_2023(q_hs_H_d_t)
        else:
            # (11) 定格暖房能力運転時
            e_r_rtd_H = dc_a.get_e_r_rtd_H(e_th_rtd_H, q_hs_rtd_H, P_hs_rtd_H, P_fan_rtd_H)
            # (15) 最小暖房能力運転時
            e_r_min_H = dc_a.get_e_r_min_H(e_r_rtd_H)
            # (13) 中間暖房能力運転時
            e_r_mid_H = dc_a.get_e_r_mid_H(e_r_rtd_H, e_th_mid_H, q_hs_mid_H, P_hs_mid_H, P_fan_mid_H, EquipmentSpec)
            # (9) 日付dの時刻tにおける暖房時
            e_r_H_d_t = dc_a.get_e_r_H_d_t(q_hs_H_d_t, q_hs_rtd_H, q_hs_min_H, q_hs_mid_H, e_r_mid_H, e_r_min_H, e_r_rtd_H)

        """ E_E: 日付dの時刻tにおける1時間当たりの暖房時の消費電力量 (kWh/h) """

        # (37) 送風機の付加分（kWh/h）
        E_E_fan_H_d_t = dc_a.get_E_E_fan_H_d_t(type, P_fan_rtd_H, V_hs_vent_d_t, V_hs_supply_d_t, V_hs_dsgn_H, q_hs_H_d_t, f_SFP_H)

        # (5) 圧縮機の分
        E_E_comp_H_d_t = dc_a.get_E_E_comp_H_d_t(
                            q_hs_H_d_t,
                            e_hs_H_d_t = dc_a.get_e_hs_H_d_t(e_th_H_d_t, e_r_H_d_t))  # (7) 日付dの時刻tにおける暖房時の熱源機の効率(-)
        E_E_H_d_t = E_E_comp_H_d_t + E_E_fan_H_d_t  # (1)

    elif type == PROCESS_TYPE_2 or type == PROCESS_TYPE_4:
        # TODO: f_SFP_H: type2のみのパラメータ type4での使用は怪しい
        # NOTE: ルームエアコンでは V_hs_vent(換気風量) は使用されません

        if type == PROCESS_TYPE_2:
            E_E_CRAC_H_d_t = \
                rac.calc_E_E_H_d_t(region,
                                   q_rtd_C, q_rtd_H, q_max_C, q_max_H,  # q[W]
                                   e_rtd_H, dualcompressor_H,
                                   q_hs_H_d_t * 3.6/1000,  # L_H[MJ/h]
                                   input_C_af_H, climateFile)
            E_E_fan_H_d_t = \
                dc_a.get_E_E_fan_H_d_t(type, P_rac_fan_rtd_H, V_hs_vent_d_t, V_hs_supply_d_t, V_hs_dsgn_H,
                                       q_hs_H_d_t,  # q[W]
                                       f_SFP_H)

        elif type == PROCESS_TYPE_4:
            # 『2.2 実験方法と実験条件』より
            # 最大時の給気風量と機器のカタログ公表値(強)の比
            V_ratio1 = (spec.V_inner * 60) / np.max(V_hs_supply_d_t)
            # 室外機/室内機 風量比
            V_ratio2 = spec.V_outer / spec.V_inner

            COP_H_d_t = denchu_2.calc_COP_H_d_t(
                                q_d_t= q_hs_H_d_t / 1000,
                                P_rac_fan_rtd= P_rac_fan_rtd_H / 1000,
                                R= simu_R_H,
                                V_rac_inner_d_t= V_ratio1 * V_hs_supply_d_t,
                                V_rac_outer_d_t= V_ratio2 * V_ratio1 * V_hs_supply_d_t,
                                region= region,
                                Theta_real_inner= Theta_real_inner,
                                RH_real_inner= RH_real_inner,
                                climateFile= climateFile)
            E_E_CRAC_H_d_t = np.divide(q_hs_H_d_t / 1000,  # kW
                                       COP_H_d_t,
                                       out=np.zeros_like(q_hs_H_d_t),
                                       where=COP_H_d_t!=0)  # kWh

            # (37) 送風機の付加分（kWh/h）
            # NOTE: 求めたいのは循環ファンなので P_rac_fan ではなく P_fan を使用する
            E_E_fan_H_d_t = dc_a.get_E_E_fan_H_d_t(type, P_fan_rtd_H, V_hs_vent_d_t, V_hs_supply_d_t, V_hs_dsgn_H, q_hs_H_d_t, f_SFP_H)

            df_output_denchuH = pd.DataFrame(index = pd.date_range(
                datetime(2023,1,1,1,0,0), datetime(2024,1,1,0,0,0), freq='h'))

            df_output_denchuH = df_output_denchuH.assign(
                q_hs_H_d_t = q_hs_H_d_t,  # W
                COP_H_d_t = COP_H_d_t,
                E_E_CRAC_H_d_t = E_E_CRAC_H_d_t,  # kW
                E_E_fan_H_d_t = E_E_fan_H_d_t,  # kW
                E_E_H_d_t = E_E_CRAC_H_d_t + E_E_fan_H_d_t  # kW
            )
            df_output_denchuH.to_csv(case_name + version_info() + '_denchu_H_output.csv', encoding='cp932')  # =Shift_JIS

        E_E_H_d_t = E_E_CRAC_H_d_t + E_E_fan_H_d_t

    else:
        raise Exception('暖房設備機器の種類の入力が不正です。')

    return E_E_H_d_t, q_hs_H_d_t, E_E_fan_H_d_t

# TODO: この関数に Q_hat_hs_d_t が使用されないことが妥当でしょうか?
def calc_E_E_C_d_t(
        case_name,
        Theta_hs_out_d_t, Theta_hs_in_d_t, Theta_ex_d_t,  # 空気温度
        V_hs_supply_d_t, V_hs_vent_d_t, V_hs_dsgn_C,      # 風量
        X_hs_out_d_t, X_hs_in_d_t,                        # 絶対湿度
        q_hs_min_C,                                       # 最小冷房時
        q_hs_mid_C, P_hs_mid_C, V_fan_mid_C, P_fan_mid_C,  # 中間冷房時
        q_max_C,                                           # 最大冷房時
        q_hs_rtd_C, P_hs_rtd_C, V_fan_rtd_C, P_fan_rtd_C, q_rtd_C, e_rtd_C, P_rac_fan_rtd_C,  # 定格冷房時
        type, region, dualcompressor_C, EquipmentSpec, input_C_af_C, f_SFP_C, climateFile,  # その他
        simu_R_C=None, spec: Spec=None, Theta_real_inner=None, RH_real_inner=None):  # 電中研モデルのみ使用
    """ (1)
    Args:
        P_fan_rad_C: 定格冷房能力試験 室内側送風機の消費電力 [W]\n
        日付dの時刻tにおける\n
            V_hs_vent_d_t: 熱源機の風量のうちの全般換気分 [m3/h]\n
            V_hs_supply_d_t: 熱源機の風量 [m3/h]\n
            X_hs_in_d_t: 熱源機の入口における絶対湿度 [kg/kg(DA)]\n
            f_SFP_C: ファンの比消費電力 [W/(m3/h)]\n
    Returns:
        日付dの時刻tにおける\n
            E_E_C_d_t: 1時間当たりの 冷房時の消費電力量 [kWh/h]\n
            E_E_fan_C_d_t: 1時間当たりの 冷房時消費電力量の送風機による付加分 [kWh/h]\n
            q_hs_CS_d_t: 1時間当たりの 熱源機の平均冷房 顕熱能力 [W]\n
            q_hs_CL_d_t: 1時間当たりの 熱源機の平均冷房 潜熱能力 [W]\n
    """
    # (4) 日付dの時刻tにおける1時間当たりの熱源機の平均冷房能力(-)
    q_hs_CS_d_t, q_hs_CL_d_t = dc_a.get_q_hs_C_d_t_2(Theta_hs_out_d_t, Theta_hs_in_d_t, X_hs_out_d_t, X_hs_in_d_t, V_hs_supply_d_t, region)

    _logger.NDdebug("V_hs_supply_d_t", V_hs_supply_d_t)

    if type == PROCESS_TYPE_1 or type == PROCESS_TYPE_3:
        """ 顕熱/潜熱 (CS/CL) を使用せずに 全熱負荷(C) を再計算して使用する """

        # (4)
        q_hs_C_d_t = dc_a.get_q_hs_C_d_t(Theta_hs_out_d_t, Theta_hs_in_d_t, X_hs_out_d_t, X_hs_in_d_t, V_hs_supply_d_t, region)
        _logger.NDdebug("q_hs_C_d_t", q_hs_C_d_t)

        """ e_th: ヒートポンプサイクルの理論効率(-) """

        # (22) 中間冷房能力運転時
        e_th_mid_C = dc_a.calc_e_th_mid_C(type, V_fan_mid_C, q_hs_mid_C, q_hs_rtd_C)
        # (21) 定格冷房能力運転時
        e_th_rtd_C = dc_a.calc_e_th_rtd_C(type, V_fan_rtd_C, q_hs_rtd_C)
        # (18) 日付dの時刻tにおける暖房時
        e_th_C_d_t = dc_a.calc_e_th_C_d_t(type, Theta_ex_d_t, Theta_hs_in_d_t, X_hs_in_d_t, Theta_hs_out_d_t, V_hs_supply_d_t, q_hs_rtd_C)

        """ e_r: ヒートポンプサイクルの理論効率に対する熱源機の効率の比(-) """

        if type == PROCESS_TYPE_1:
            # (11) 定格冷房能力運転時
            e_r_rtd_C = dc_a.get_e_r_rtd_C(e_th_rtd_C, q_hs_rtd_C, P_hs_rtd_C, P_fan_rtd_C)
            # (15) 最小冷房能力運転時
            e_r_min_C = dc_a.get_e_r_min_C(e_r_rtd_C)
            # (13) 定格冷房能力運転時
            e_r_mid_C = dc_a.get_e_r_mid_C(e_r_rtd_C, e_th_mid_C, q_hs_mid_C, P_hs_mid_C, P_fan_mid_C, EquipmentSpec)
            # (9) 日付dの時刻tにおける冷房時
            e_r_C_d_t = dc_a.get_e_r_C_d_t(q_hs_C_d_t, q_hs_rtd_C, q_hs_min_C, q_hs_mid_C, e_r_mid_C, e_r_min_C, e_r_rtd_C)

        elif type == PROCESS_TYPE_3:  #コンプレッサ効率特性
            # TODO: 潜熱評価モデルが 潜熱(q_hs_CL) ではなく 全熱(q_hs_C) を使用してOKか確認
            e_r_C_d_t = dc_a.get_e_r_C_d_t_2023(q_hs_C_d_t)  # 日付dの時刻tにおける冷房時

        """ E_E: 日付dの時刻tにおける1時間当たりの冷房時の消費電力量 (kWh/h) """

        # (38) 送風機の付加分 (kWh/h)
        E_E_fan_C_d_t = dc_a.get_E_E_fan_C_d_t(type, P_fan_rtd_C, V_hs_vent_d_t, V_hs_supply_d_t, V_hs_dsgn_C, q_hs_C_d_t, f_SFP_C)

        # (6) 圧縮機の分
        E_E_comp_C_d_t = dc_a.get_E_E_comp_C_d_t(
                            q_hs_C_d_t,
                            e_hs_C_d_t = dc_a.get_e_hs_C_d_t(e_th_C_d_t, e_r_C_d_t))  # (8)

        _logger.NDdebug("E_E_comp_C_d_t", E_E_comp_C_d_t)
        _logger.NDdebug("E_E_fan_C_d_t", E_E_fan_C_d_t)
        E_E_C_d_t = E_E_comp_C_d_t + E_E_fan_C_d_t  # (2)

    elif type == PROCESS_TYPE_2 or type == PROCESS_TYPE_4:
        """ 顕熱/潜熱 (CS/CL) を使用する """
        # NOTE: ルームエアコンでは V_hs_vent(換気風量) は使用されません

        if type == PROCESS_TYPE_2:
            E_E_CRAC_C_d_t = \
                rac.calc_E_E_C_d_t(region, q_rtd_C, q_max_C,  # q[W]
                                   e_rtd_C, dualcompressor_C,
                                   q_hs_CS_d_t * 3.6/1000, q_hs_CL_d_t * 3.6/1000,  # L_H[MJ/h]
                                   input_C_af_C, climateFile)
            # (38) 送風機の付加分 (kWh/h)
            E_E_fan_C_d_t = \
                dc_a.get_E_E_fan_C_d_t(type, P_rac_fan_rtd_C,
                                       V_hs_vent_d_t, V_hs_supply_d_t, V_hs_dsgn_C,
                                       (q_hs_CS_d_t + q_hs_CL_d_t),  # q[W]
                                       f_SFP_C)

        elif type == PROCESS_TYPE_4:
            # 『2.2 実験方法と実験条件』より
            # 最大時の給気風量と機器のカタログ公表値(強)の比
            V_ratio1 = (spec.V_inner * 60) / np.max(V_hs_supply_d_t)
            # 室外機/室内機 風量比
            V_ratio2 = spec.V_outer / spec.V_inner

            q_hs_C_d_t = q_hs_CS_d_t + q_hs_CL_d_t

            # FIXME: COPが大きすぎる問題があります
            COP_C_d_t = denchu_2.calc_COP_C_d_t(
                            q_d_t= q_hs_C_d_t / 1000,
                            P_rac_fan_rtd= P_rac_fan_rtd_C / 1000,
                            R= simu_R_C,
                            V_rac_inner_d_t= V_ratio1 * V_hs_supply_d_t,
                            V_rac_outer_d_t= V_ratio2 * V_ratio1 * V_hs_supply_d_t,
                            region= region,
                            Theta_real_inner= Theta_real_inner,
                            RH_real_inner= RH_real_inner,
                            climateFile= climateFile)
            E_E_CRAC_C_d_t = np.divide(q_hs_C_d_t / 1000,  # kW
                                COP_C_d_t,
                                out=np.zeros_like(q_hs_C_d_t),
                                where=COP_C_d_t!=0)  # kWh

            # (38) 送風機の付加分 (kWh/h)
            E_E_fan_C_d_t = dc_a.get_E_E_fan_C_d_t(type, P_fan_rtd_C, V_hs_vent_d_t, V_hs_supply_d_t, V_hs_dsgn_C, q_hs_C_d_t, f_SFP_C)

            df_output_denchuC = pd.DataFrame(index = pd.date_range(
                datetime(2023,1,1,1,0,0), datetime(2024,1,1,0,0,0), freq='h'))

            df_output_denchuC = df_output_denchuC.assign(
                q_hs_C_d_t = q_hs_C_d_t,  # W
                COP_C_d_t = COP_C_d_t,
                E_E_CRAC_C_d_t = E_E_CRAC_C_d_t,  # kW
                E_E_fan_C_d_t = E_E_fan_C_d_t,  # kW
                E_E_C_d_t = E_E_CRAC_C_d_t + E_E_fan_C_d_t  # kW
            )
            df_output_denchuC.to_csv(case_name + version_info() + '_denchu_C_output.csv', encoding='cp932')  # =Shift_JIS

        _logger.NDdebug("E_E_CRAC_C_d_t", E_E_CRAC_C_d_t)
        _logger.NDdebug("E_E_fan_C_d_t", E_E_fan_C_d_t)
        E_E_C_d_t = E_E_CRAC_C_d_t + E_E_fan_C_d_t  # (2)

    else:
        raise Exception('冷房設備機器の種類の入力が不正です。')

    return E_E_C_d_t, E_E_fan_C_d_t, q_hs_CS_d_t, q_hs_CL_d_t
