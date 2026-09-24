import matplotlib.pyplot as plt
import numpy as np

# مختصات گره‌ها: سطر اول مختصات X و سطر دوم مختصات Y
node_x = np.array([0, 4])
node_y = np.array([0, 3])

# محاسبه اختلاف مختصات و طول عضو
delta_x = node_x[1] - node_x[0]
delta_y = node_y[1] - node_y[0]
L = np.sqrt(delta_x**2 + delta_y**2)
print("طول عضو:", L, "متر")

# محاسبه کسینوس و سینوس زاویه عضو
c = delta_x / L
s = delta_y / L
direction = np.array([c, s])
print("Direction Vector [c, s]:", direction)
print("c**2 + s**2:", c**2 + s**2)

# ساخت بردار سطر انتقالی عضو
lambda_vec = np.array([-c, -s, c, s])
print("Lambda vector:", lambda_vec)
print("Lambda vector shape:", lambda_vec.shape)

# مختصات گره دوم پس از تغییرشکل
node_x_deformed = np.array([0, 4.05])
node_y_deformed = np.array([0, 2.98])

# رسم سازه اولیه و سازه تغییرشکل‌یافته
plt.plot(node_x, node_y, "k--", linewidth=2, label="Undeformed")
plt.plot(
	node_x_deformed,
	node_y_deformed,
	"r-o",
	linewidth=2,
	markersize=8,
	label="Deformed",
)

# تنظیمات نمودار
plt.xlabel("X (m)")
plt.ylabel("Y (m)")
plt.title("Single Truss Element")
plt.grid(True)
plt.axis("equal")  # حفظ مقیاس واقعی ابعاد
plt.legend()

# نمایش پنجره رسم
plt.show()

E = 200e9   # Pa
A = 0.001   # m^2

# ۱. محاسبه سختی محوری
k_axial = (E * A) / L

# ۲. محاسبه ماتریس سختی ۴ در ۴ با ضرب خارجی
k_element = k_axial * np.outer(lambda_vec, lambda_vec)

print("Element Stiffness Matrix shape:", k_element.shape)
print("Element Stiffness Matrix (k_element):\n", k_element)

is_symmetric = np.allclose(k_element, k_element.T)
print("Is the element stiffness matrix symmetric?:", is_symmetric)
print("Determinant of k_element:", np.linalg.det(k_element))
