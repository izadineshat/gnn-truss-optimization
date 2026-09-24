import numpy as np

# تعریف ماتریس سختی و بردار نیروی کاهش‌یافته
K_reduced = np.array([[10**7]])
F_reduced = np.array([100.0])

# حل معادله کاهش‌یافته برای به دست آوردن جابجایی
u_reduced = np.linalg.solve(K_reduced, F_reduced)

# نمایش نتیجه
print("Calculated Displacement (u_2):", u_reduced)
