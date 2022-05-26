import numpy as np
import pandas as pd

from pyhees.section3_2_8 import get_r_env
from pyhees.section11_1 import calc_h_ex, load_climate, load_outdoor, get_Theta_ex, get_X_ex, get_J

# ダクト式セントラル空調機
import pyhees.section4_2 as dc
import pyhees.section4_2_a as dc_a

# エアーコンディショナー
import pyhees.section4_3 as rac

# 床下
import pyhees.section3_1_e as uf
import pyhees.section3_1 as ld

def calc_Q_UT_A(A_A, A_MR, A_OR, A_env, mu_H, mu_C, q_hs_rtd_H, q_hs_rtd_C, q_rtd_H, q_rtd_C, q_max_H, q_max_C, V_hs_dsgn_H, V_hs_dsgn_C, Q,
            VAV, general_ventilation, hs_CAV, duct_insulation, region, L_H_d_t_i, L_CS_d_t_i, L_CL_d_t_i,
            type, input_C_af_H, input_C_af_C, underfloor_insulation, underfloor_air_conditioning_air_supply, YUCACO_r_A_ufvnt, climateFile, outdoorFile):
    """未処理負荷と機器の計算に必要な変数を取得"""

    # 外気条件
    if outdoorFile == '-':
        outdoor = load_outdoor()
        Theta_ex_d_t = get_Theta_ex(region, outdoor)
        X_ex_d_t = get_X_ex(region, outdoor)
    else:
        outdoor = pd.read_csv(outdoorFile, skiprows=4, nrows=24 * 365,
            names=('day', 'hour', 'holiday', 'Theta_ex_1', 'X_ex_1'))
        Theta_ex_d_t = outdoor['Theta_ex_1'].values
        X_ex_d_t = outdoor['X_ex_1'].values

    if climateFile == '-':
        climate = load_climate(region)
    else:
        climate = pd.read_csv(climateFile, nrows=24 * 365)

    J_d_t = get_J(climate)
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
    if type == 'ダクト式セントラル空調機':
        # (38)
        Q_hs_rtd_C = dc.get_Q_hs_rtd_C(q_hs_rtd_C)

        # (37)
        Q_hs_rtd_H = dc.get_Q_hs_rtd_H(q_hs_rtd_H)
    elif type == 'ルームエアコンディショナ活用型全館空調システム':
        # (38)　冷房時の熱源機の定格出力
        Q_hs_rtd_C = dc.get_Q_hs_rtd_C(q_rtd_C)             #ルームエアコンディショナの定格能力 q_rtd_C を入力するよう書き換え

        # (37)　暖房時の熱源機の定格出力
        Q_hs_rtd_H = dc.get_Q_hs_rtd_H(q_rtd_H)             #ルームエアコンディショナの定格能力 q_rtd_H を入力するよう書き換え
    else:
        raise Exception('設備機器の種類の入力が不正です。')
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
        V_dash_hs_supply_d_t = dc.get_V_dash_hs_supply_d_t(V_hs_min, updated_V_hs_dsgn_H, updated_V_hs_dsgn_C, Q_hs_rtd_H, Q_hs_rtd_C, Q_hat_hs_d_t, region)

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
    if type == 'ダクト式セントラル空調機':
        # (33)
        L_star_CL_d_t = dc.get_L_star_CL_d_t(L_star_CL_d_t_i)

        # (32)
        L_star_CS_d_t = dc.get_L_star_CS_d_t(L_star_CS_d_t_i)

        # (31)
        L_star_CL_max_d_t = dc.get_L_star_CL_max_d_t(L_star_CS_d_t)

        # (30)
        L_star_dash_CL_d_t = dc.get_L_star_dash_CL_d_t(L_star_CL_max_d_t, L_star_CL_d_t)

        # (29)
        L_star_dash_C_d_t = dc.get_L_star_dash_C_d_t(L_star_CS_d_t, L_star_dash_CL_d_t)

        # (28)
        SHF_dash_d_t = dc.get_SHF_dash_d_t(L_star_CS_d_t, L_star_dash_C_d_t)

        # (27)
        Q_hs_max_C_d_t = dc.get_Q_hs_max_C_d_t(q_hs_rtd_C)

        # (26)
        Q_hs_max_CL_d_t = dc.get_Q_hs_max_CL_d_t(Q_hs_max_C_d_t, SHF_dash_d_t, L_star_dash_CL_d_t)

        # (25)
        Q_hs_max_CS_d_t = dc.get_Q_hs_max_CS_d_t(Q_hs_max_C_d_t, SHF_dash_d_t)

        # (24)
        C_df_H_d_t = dc.get_C_df_H_d_t(Theta_ex_d_t, h_ex_d_t)

        # (23)
        Q_hs_max_H_d_t = dc.get_Q_hs_max_H_d_t(q_hs_rtd_H, C_df_H_d_t)
    elif type == 'ルームエアコンディショナ活用型全館空調システム':
        # (24)　デフロストに関する暖房出力補正係数
        C_df_H_d_t = dc.get_C_df_H_d_t(Theta_ex_d_t, h_ex_d_t)

        # 最大暖房能力比
        q_r_max_H = rac.get_q_r_max_H(q_max_H, q_rtd_H)

        # 最大暖房出力比
        Q_r_max_H_d_t = rac.calc_Q_r_max_H_d_t(q_rtd_C, q_r_max_H, Theta_ex_d_t)

        # 最大暖房出力
        Q_max_H_d_t = rac.calc_Q_max_H_d_t(Q_r_max_H_d_t, q_rtd_H, Theta_ex_d_t, h_ex_d_t, input_C_af_H)
        Q_hs_max_H_d_t = Q_max_H_d_t

        # 最大冷房能力比
        q_r_max_C = rac.get_q_r_max_C(q_max_C, q_rtd_C)

        # 最大冷房出力比
        Q_r_max_C_d_t = rac.calc_Q_r_max_C_d_t(q_r_max_C, q_rtd_C, Theta_ex_d_t)

        # 最大冷房出力
        Q_max_C_d_t = rac.calc_Q_max_C_d_t(Q_r_max_C_d_t, q_rtd_C, input_C_af_C)

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
    else:
        raise Exception('設備機器の種類の入力が不正です。')
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

    if underfloor_air_conditioning_air_supply:
        Theta_uf_d_t, Theta_g_surf_d_t = uf.calc_Theta(region, A_A, A_MR, A_OR, Q, YUCACO_r_A_ufvnt, underfloor_insulation, Theta_req_d_t_i[0], Theta_ex_d_t,
                                                V_dash_supply_d_t_i[0], '', L_H_d_t_i, L_CS_d_t_i)
        Theta_req_d_t_i[0] += (Theta_req_d_t_i[0] - Theta_uf_d_t)
        Theta_uf_d_t, Theta_g_surf_d_t = uf.calc_Theta(region, A_A, A_MR, A_OR, Q, YUCACO_r_A_ufvnt, underfloor_insulation, Theta_req_d_t_i[1], Theta_ex_d_t,
                                                V_dash_supply_d_t_i[1], '', L_H_d_t_i, L_CS_d_t_i)
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

    if underfloor_air_conditioning_air_supply:
        Theta_uf_d_t, Theta_g_surf_d_t = uf.calc_Theta(region, A_A, A_MR, A_OR, Q, YUCACO_r_A_ufvnt, underfloor_insulation, Theta_supply_d_t_i[0], Theta_ex_d_t,
                                                V_dash_supply_d_t_i[0], '', L_H_d_t_i, L_CS_d_t_i)
        Theta_supply_d_t_i[0] -= (Theta_supply_d_t_i[0] - Theta_uf_d_t)
        Theta_uf_d_t, Theta_g_surf_d_t = uf.calc_Theta(region, A_A, A_MR, A_OR, Q, YUCACO_r_A_ufvnt, underfloor_insulation, Theta_supply_d_t_i[1], Theta_ex_d_t,
                                                V_dash_supply_d_t_i[1], '', L_H_d_t_i, L_CS_d_t_i)
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
    Q_UT_CS_d_t_i = dc.get_Q_UT_CS_d_t_i(L_star_CS_d_t_i, L_dash_CS_d_t_i)

    # (2)　暖房設備機器等の未処理暖房負荷
    Q_UT_H_d_t_i = dc.get_Q_UT_H_d_t_i(L_star_H_d_t_i, L_dash_H_d_t_i)

    # (1)　冷房設備の未処理冷房負荷の設計一次エネルギー消費量相当値
    E_C_UT_d_t = dc.get_E_C_UT_d_t(Q_UT_CL_d_t_i, Q_UT_CS_d_t_i, region)

    return E_C_UT_d_t, Q_UT_H_d_t_i, Q_UT_CS_d_t_i, Q_UT_CL_d_t_i, Theta_hs_out_d_t, Theta_hs_in_d_t, Theta_ex_d_t, \
           X_hs_out_d_t, X_hs_in_d_t, V_hs_supply_d_t, V_hs_vent_d_t, C_df_H_d_t

def calc_E_E_H_d_t(Theta_hs_out_d_t, Theta_hs_in_d_t, Theta_ex_d_t, V_hs_supply_d_t, V_hs_vent_d_t, C_df_H_d_t, V_hs_dsgn_H,
        EquipmentSpec, q_hs_rtd_H, P_hs_rtd_H, V_fan_rtd_H, P_fan_rtd_H, q_hs_mid_H, P_hs_mid_H, V_fan_mid_H, P_fan_mid_H, q_hs_min_H,
        region, type, q_rtd_C, q_rtd_H, P_rac_fan_rtd_H, e_rtd_H, dualcompressor_H, input_C_af_H, f_SFP_H):
    """日付dの時刻tにおける1時間当たりの暖房時の消費電力量（kWh/h）(1)"""

    # (3)
    q_hs_H_d_t = dc_a.get_q_hs_H_d_t(Theta_hs_out_d_t, Theta_hs_in_d_t, V_hs_supply_d_t, C_df_H_d_t, region)

    if type == 'ダクト式セントラル空調機':
        # (37)
        E_E_fan_H_d_t = dc_a.get_E_E_fan_H_d_t(P_fan_rtd_H, V_hs_vent_d_t, V_hs_supply_d_t, V_hs_dsgn_H, q_hs_H_d_t * 3.6 / 1000, f_SFP_H)

        # (20)
        e_th_mid_H = dc_a.calc_e_th_mid_H(V_fan_mid_H, q_hs_mid_H)
    
        # (19)
        e_th_rtd_H = dc_a.calc_e_th_rtd_H(V_fan_rtd_H, q_hs_rtd_H)
    
        # (17)
        e_th_H_d_t = dc_a.calc_e_th_H_d_t(Theta_ex_d_t, Theta_hs_in_d_t, Theta_hs_out_d_t, V_hs_supply_d_t)
    
        # (11)
        e_r_rtd_H = dc_a.get_e_r_rtd_H(e_th_rtd_H, q_hs_rtd_H, P_hs_rtd_H, P_fan_rtd_H)
    
        # (15)
        e_r_min_H = dc_a.get_e_r_min_H(e_r_rtd_H)
    
        # (13)
        e_r_mid_H = dc_a.get_e_r_mid_H(e_r_rtd_H, e_th_mid_H, q_hs_mid_H, P_hs_mid_H, P_fan_mid_H, EquipmentSpec)
    
        # (9)
        e_r_H_d_t = dc_a.get_e_r_H_d_t(q_hs_H_d_t, q_hs_rtd_H, q_hs_min_H, q_hs_mid_H, e_r_mid_H, e_r_min_H, e_r_rtd_H)
    
        # (7)
        e_hs_H_d_t = dc_a.get_e_hs_H_d_t(e_th_H_d_t, e_r_H_d_t)
    
        # (5)
        E_E_comp_H_d_t = dc_a.get_E_E_comp_H_d_t(q_hs_H_d_t, e_hs_H_d_t)
    
        # (1)
        E_E_H_d_t = E_E_comp_H_d_t + E_E_fan_H_d_t
    elif type == 'ルームエアコンディショナ活用型全館空調システム':
        E_E_fan_H_d_t = dc_a.get_E_E_fan_H_d_t(P_rac_fan_rtd_H, V_hs_vent_d_t, V_hs_supply_d_t, V_hs_dsgn_H, q_hs_H_d_t * 3.6 / 1000, f_SFP_H)
        E_E_CRAC_H_d_t = rac.calc_E_E_H_d_t(region, q_rtd_C, q_rtd_H, e_rtd_H, dualcompressor_H, q_hs_H_d_t * 3.6 / 1000, input_C_af_H)
        E_E_H_d_t = E_E_CRAC_H_d_t + E_E_fan_H_d_t
    else:
        raise Exception('暖房設備機器の種類の入力が不正です。')

    return E_E_H_d_t, q_hs_H_d_t, E_E_fan_H_d_t

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

def get_E_E_C_d_t(Theta_hs_out_d_t, Theta_hs_in_d_t, Theta_ex_d_t, X_hs_out_d_t, X_hs_in_d_t, V_hs_supply_d_t, V_hs_vent_d_t, V_hs_dsgn_C,
        EquipmentSpec, q_hs_rtd_C, P_hs_rtd_C, V_fan_rtd_C, P_fan_rtd_C, q_hs_mid_C, P_hs_mid_C, V_fan_mid_C, P_fan_mid_C, q_hs_min_C,
        region, type, q_rtd_C, e_rtd_C, P_rac_fan_rtd_C, input_C_af_C, dualcompressor_C, f_SFP_C):

    # (4)
    q_hs_CS_d_t, q_hs_CL_d_t = get_q_hs_C_d_t_2(Theta_hs_out_d_t, Theta_hs_in_d_t, X_hs_out_d_t, X_hs_in_d_t, V_hs_supply_d_t, region)

    if type == 'ダクト式セントラル空調機':
        # (4)
        q_hs_C_d_t = dc_a.get_q_hs_C_d_t(Theta_hs_out_d_t, Theta_hs_in_d_t, X_hs_out_d_t, X_hs_in_d_t, V_hs_supply_d_t, region)

        # (38)
        E_E_fan_C_d_t = dc_a.get_E_E_fan_C_d_t(P_fan_rtd_C, V_hs_vent_d_t, V_hs_supply_d_t, V_hs_dsgn_C, q_hs_C_d_t, f_SFP_C)

        # (22)
        e_th_mid_C = dc_a.calc_e_th_mid_C(V_fan_mid_C, q_hs_mid_C)

        # (21)
        e_th_rtd_C = dc_a.calc_e_th_rtd_C(V_fan_rtd_C, q_hs_rtd_C)

        # (18)
        e_th_C_d_t = dc_a.calc_e_th_C_d_t(Theta_ex_d_t, Theta_hs_in_d_t, X_hs_in_d_t, Theta_hs_out_d_t, V_hs_supply_d_t)

        # (12)
        e_r_rtd_C = dc_a.get_e_r_rtd_C(e_th_rtd_C, q_hs_rtd_C, P_hs_rtd_C, P_fan_rtd_C)

        # (16)
        e_r_min_C = dc_a.get_e_r_min_C(e_r_rtd_C)

        # (14)
        e_r_mid_C = dc_a.get_e_r_mid_C(e_r_rtd_C, e_th_mid_C, q_hs_mid_C, P_hs_mid_C, P_fan_mid_C, EquipmentSpec)

        # (10)
        e_r_C_d_t = dc_a.get_e_r_C_d_t(q_hs_C_d_t, q_hs_rtd_C, q_hs_min_C, q_hs_mid_C, e_r_mid_C, e_r_min_C, e_r_rtd_C)

        # (8)
        e_hs_C_d_t = dc_a.get_e_hs_C_d_t(e_th_C_d_t, e_r_C_d_t)

        # (6)
        E_E_comp_C_d_t = dc_a.get_E_E_comp_C_d_t(q_hs_C_d_t, e_hs_C_d_t)

        # (2)
        E_E_C_d_t = E_E_comp_C_d_t + E_E_fan_C_d_t
    elif type == 'ルームエアコンディショナ活用型全館空調システム':
        E_E_CRAC_C_d_t = rac.calc_E_E_C_d_t(region, q_rtd_C, e_rtd_C, dualcompressor_C, q_hs_CS_d_t * 3.6 / 1000, q_hs_CL_d_t * 3.6 / 1000, input_C_af_C)

        # (38)
        E_E_fan_C_d_t = dc_a.get_E_E_fan_C_d_t(P_rac_fan_rtd_C, V_hs_vent_d_t, V_hs_supply_d_t, V_hs_dsgn_C, q_hs_CS_d_t * 3.6 / 1000 + q_hs_CL_d_t * 3.6 / 1000, f_SFP_C)

        # (2)
        E_E_C_d_t = E_E_CRAC_C_d_t + E_E_fan_C_d_t
    else:
        raise Exception('冷房設備機器の種類の入力が不正です。')

    return E_E_C_d_t, E_E_fan_C_d_t, q_hs_CS_d_t, q_hs_CL_d_t
