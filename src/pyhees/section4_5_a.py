# ============================================================================
# 付録 A 機器の性能を表す仕様の決定方法
# ============================================================================

# ============================================================================
# A.1 敷設面積
# ============================================================================

# 敷設面積 A_f
def get_A_f(A_HCZ, r_Af = None):
    """敷設面積

    Args:
      A_HCZ(float): 暖冷房区画の床面積 (m2)
      r_Af(float): 床暖房パネルの敷設率

    Returns:
      float: 敷設面積

    """
    if r_Af is None:
        r_Af = 0.4

    return A_HCZ * r_Af  # (1)


# 床暖房パネルの敷設率 r_Af
def get_r_Af(A_f, A_HCZ):
    """[summary]

    Args:
      A_f(float): 敷設面積
      A_HCZ(float): 暖冷房区画の床面積 (m2)

    Returns:
      float: 床暖房パネルの敷設率

    """
    return A_f / A_HCZ  # (2)


# ============================================================================
# A.2 上面放熱率
# ============================================================================

# def get_r_up():
#     r_up = 1.0 - H * (R_si + R_U) * R_U     #(3)
#     return (r_up * 100) / 100

# 2) 温度差係数U

if __name__ == '__main__':
    A_HCZ = 120.08
    A_f = 0.8

    # 床暖房パネルの敷設率
    r_Af = get_r_Af(A_f, A_HCZ)

    # 敷設面積
    A_f = get_A_f(A_HCZ, r_Af)

    print('A_HCZ = {}'.format(A_HCZ))
    print('A_f = {}'.format(A_f))
    print('r_Af = {}'.format(r_Af))
    print('A_f = {}'.format(A_f))
