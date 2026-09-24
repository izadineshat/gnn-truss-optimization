import numpy as np

# ۱. تعریف ماتریس سختی K
K = np.array([[200, -50], [-50, 150]])

# ۲. تعریف بردار جابجایی گره‌ها (واحد: متر)
u = np.array([0.02, 0.01])  # جابجایی گره‌ها

# ۳. ضرب ماتریس در بردار با عملگر @
F = K @ u  # ضرب ماتریس سختی در بردار جابجایی

print("Displacement vector u:", u)
print("Shape of u:", u.shape)
print("Resulting Force vector F:", F)
print("Shape of F:", F.shape)

# ۴. محاسبه جابجایی گره‌ها با استفاده از ماتریس سختی و بردار نیرو
u_calculated = np.linalg.solve(K, F)  # حل معادله K * u = F برای به‌دست‌آوردن u
print("Calculated Displacement vector u:", u_calculated)

# ۵. تعریف ماتریس مجاورت خرپای مثلثی سه‌گرهی
A = np.array([
	[0, 1, 1],
	[1, 0, 1],
	[1, 1, 0]
])

print("Adjacency matrix A:")
print(A)
print("Shape of A:", A.shape)

# ۶. محاسبه درجه گره‌ها و ساخت ماتریس قطری درجه
degrees = np.sum(A, axis=1)
D = np.diag(degrees)

print("Node degrees:", degrees)
print("Degree matrix D:")
print(D)

# ۷. محاسبه ماتریس لاپلاسین و بررسی مجموع سطرها

L = D - A
row_sums = np.sum(L, axis=1)

print("Laplacian matrix L:")
print(L)

print("Row sums of L:", row_sums)

# ۸. نمایش اعضای خرپا در قالب edge_index
# شماره‌گذاری گره‌ها در پایتون از صفر شروع می‌شود: ۰، ۱ و ۲
# هر ستون یک اتصال را نشان می‌دهد؛ ردیف اول مبدأ و ردیف دوم مقصد است.
# هر عضو در دو جهت آمده است تا اتصال بدون‌جهت خرپا نمایش داده شود.
edge_index = np.array([
    [0, 1, 1, 2, 2, 0],
    [1, 0, 2, 1, 0, 2]
])

# آرایه باید دو ردیف و شش ستون داشته باشد:
# دو ردیف برای مبدأ و مقصد، و شش ستون برای سه عضو در دو جهت.
print("Edge index representation:")
print(edge_index)
print("Shape of edge_index:", edge_index.shape)

# ۹. تعریف ویژگی‌های گره‌ها (مختصات x و y هر گره)
# سطر ۰: مختصات گره ۰ -> (0, 0)
# سطر ۱: مختصات گره ۱ -> (4, 0)
# سطر ۲: مختصات گره ۲ -> (2, 3)
node_features = np.array([
    [0, 0],
    [4, 0],
    [2, 3]
])

print("Node features matrix (x, y coordinates):")
print(node_features)
print("Shape of node_features:", node_features.shape)

edge_attr = np.array([
    [0.002], [0.002], [0.0015],
    [0.0015], [0.001], [0.001]
], dtype=np.float32)

print(edge_attr.shape)