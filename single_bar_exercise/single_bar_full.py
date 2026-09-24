import numpy as np

# ۱. تعریف مشخصات فیزیکی و محاسبه سختی (k = EA / L)
E = 200e9  # مدول الاستیسیته (Pa)
A = 0.0001 # سطح مقطع (m^2)
L = 2.0    # طول میله (m)

k = (E * A) / L  # مقدار سختی: 10^7 N/m

# ۲. ساخت ماتریس سختی کامل سیستم (۲ در ۲)
# این ماتریس شامل تمام گره‌ها (حتی گره‌های مقید) است
K_full = np.array([
    [ k, -k],
    [-k,  k]
])

# ۳. تعریف بردار جابجایی کامل
# گره ۱ ثابت است (0.0) و گره ۲ جابجایی u2 را دارد
u2 = 100.0 / k  # مقدار جابجایی محاسبه شده برای گره ۲
u_full = np.array([0.0, u2])

# ۴. محاسبه بردار نیروها با استفاده از رابطه F = K * u
F_full = K_full @ u_full

# ۵. استخراج نتایج
F1 = F_full[0] # نیروی واکنش در تکیه‌گاه (گره ۱)
F2 = F_full[1] # نیروی اعمال شده در گره ۲

print("Full Stiffness Matrix (K):\n", K_full)
print("-" * 30)
print("Full Displacement Vector (u):", u_full)
print("-" * 30)
print("Full Force Vector (F1, F2):", F_full)
print("-" * 30)
print(f"Reaction Force at node 1 (F1): {F1} N")
print(f"Applied Force at node 2 (F2): {F2} N")
