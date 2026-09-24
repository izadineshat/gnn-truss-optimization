import numpy as np

# تعریف مختصات گره‌ها
nodes = np.array([
    [-1, -2],   # گره ۰
    [4, 3],   # گره ۱   
])
print("Nodes:\n", nodes)
print("Shape of nodes:", nodes.shape)


# استخراج مختصات گره‌ها
node1 = nodes[0]
node2 = nodes[1]

#محاسبه تفاضل مختصات
dx = node2[0] - node1[0]
dy = node2[1] - node1[1]   

# محاسبه طول عضو
L = np.sqrt(dx**2 + dy**2)
#کسینوس های هادی
c = dx / L
s = dy / L

print("Length of the member (L):", L)
print("Cosine of the angle (c):", c)
print("Sine of the angle (s):", s)


# تعریف بردار جهت با ابعاد (1, 4)
lambda_vec = np.array([-c, -s, c, s])

#سختی محوری
EA_over_L = (200e9 * 0.01) / L  # فرض شده است که E = 200 GPa و A = 0.01 m^2

#ساخت ماتریس سختی المان با ضریب ماتریسی
k_element = EA_over_L * np.outer(lambda_vec, lambda_vec)

print("Shape of k_element:", k_element.shape)
print("Is symmetric:", np.allclose(k_element, k_element.T))

#محاسبه دترمینان ماتریس سختی المان
det_k = np.linalg.det(k_element)
print("Determinant of k_element:", det_k)


# ------------------------------------------------------------------
# طول جدید عضو پس از تغییرشکل با رابطه فیثاغورس
# ------------------------------------------------------------------
# جابجایی گره‌ها بر حسب متر: گره ۰ ثابت است و گره ۱ جابجا می‌شود
u = np.array([
    [0.00,  0.00],   # جابجایی گره ۰ : (u_x, u_y)
    [0.05, -0.02],   # جابجایی گره ۱ : (u_x, u_y)
])
print("Displacements u:\n", u)

# ۱. مختصات گرهها پس از تغییرشکل = مختصات اولیه + جابجایی
nodes_new = nodes + u
print("Deformed nodes:\n", nodes_new)

# ۲. تفاضل مختصات جدید بین دو گره
dx_new = nodes_new[1, 0] - nodes_new[0, 0]
dy_new = nodes_new[1, 1] - nodes_new[0, 1]
print("dx_new:", dx_new)
print("dy_new:", dy_new)

# ۳. طول جدید با رابطه فیثاغورس:  L_new = sqrt(dx^2 + dy^2)
L_new = np.sqrt(dx_new**2 + dy_new**2)

# ۴. تغییر طول و کرنش محوری عضو
delta_L = L_new - L      # تغییر طول
strain = delta_L / L     # کرنش محوری
print("Length before deformation (L):", L)
print("Length after  deformation (L_new):", L_new)
print("Change in length (delta_L):", delta_L)
print("Axial strain (delta_L / L):", strain)

# ۵. مقایسه با تقریب خطی تغییر طول:  delta_L ~ lambda_vec . u
u_vec = u.reshape(-1)
delta_L_linear = float(lambda_vec @ u_vec)
print("delta_L (linear approx, lambda . u):", delta_L_linear)
