Theta_hs_out_max_H_d_t_limit: float = 45
"""最大暖房出力時の熱源機の出口における空気温度の最大値の上限値"""
Theta_hs_out_min_C_d_t_limit: float = 15
"""最大冷房出力時の熱源機の出口における空気温度の最低値の下限値"""
C_df_H_d_t_defrost_ductcentral: float = 0.77
"""デフロストに関する暖房出力補正係数（ダクトセントラル空調機）"""
defrost_temp_ductcentral: float = 5
"""デフロスト発生外気温度（ダクトセントラル空調機）"""
defrost_humid_ductcentral: float = 80
"""デフロスト発生外気相対湿度（ダクトセントラル空調機）"""
phi_i: float = 0.49
"""ダクトiの線熱損失係数"""
C_V_fan_dsgn_H: float = 0.79
"""暖房時の送風機の設計風量に関する係数"""
C_V_fan_dsgn_C: float = 0.79
"""冷房時の送風機の設計風量に関する係数"""
C_df_H_d_t_defrost_rac: float = 0.77
"""デフロストに関する暖房出力補正係数（ルームエアコンディショナー）"""
defrost_temp_rac: float = 5
"""デフロスト発生外気温度（ルームエアコンディショナー）"""
defrost_humid_rac: float = 80
"""デフロスト発生外気相対湿度（ルームエアコンディショナー）"""
C_af_C: float = 0.85
"""室内機吹き出し風量に関する冷房出力補正係数"""
C_hm_C: float = 1.15
"""室内機吸い込み湿度に関する冷房出力補正係数"""
q_rtd_C_limit: float = 5600
"""定格冷房能力の最大値"""

def set_constants(input: dict):
  Theta_hs_out_max_H_d_t_limit = float(input['Theta_hs_out_max_H_d_t_limit'])
  Theta_hs_out_min_C_d_t_limit = float(input['Theta_hs_out_min_C_d_t_limit'])
  C_df_H_d_t_defrost_ductcentral = float(input['C_df_H_d_t_defrost_ductcentral'])
  defrost_temp_ductcentral = float(input['defrost_temp_ductcentral'])
  defrost_humid_ductcentral = float(input['defrost_humid_ductcentral'])
  phi_i = float(input['phi_i'])
  C_V_fan_dsgn_H = float(input['C_V_fan_dsgn_H'])
  C_V_fan_dsgn_C = float(input['C_V_fan_dsgn_C'])
  C_df_H_d_t_defrost_rac = float(input['C_df_H_d_t_defrost_rac'])
  defrost_temp_rac = float(input['defrost_temp_rac'])
  defrost_humid_rac = float(input['defrost_humid_rac'])
  C_af_C = float(input['C_af_C'])
  C_hm_C = float(input['C_hm_C'])
  q_rtd_C_limit = float(input['q_rtd_C_limit'])