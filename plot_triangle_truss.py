

import matplotlib.pyplot as plt
import numpy as np

# تعریف مختصات گره‌ها
nodes = np.array([
    [0, 0], # گره ۰
    [4, 0], # گره ۱
    [2, 3]  # گره ۲
])

# بررسی ابعاد آرایه گره‌ها پس از بارگذاری در حافظه
# خروجی مورد انتظار: (۳، ۲) یعنی ۳ گره و ۲ ویژگی مختصات (x, y)
print("Nodes array:")
print(nodes)
print("Shape of nodes:", nodes.shape)
print("dtype of nodes:", nodes.dtype)

# رسم گره‌ها
plt.scatter(nodes[:, 0], nodes[:, 1], color='red', s=100, zorder=5)

# تعریف اتصالات ( اعضای خرپا)
members = [
    (0, 1), # اتصال بین گره ۰ و گره ۱
    (1, 2), # اتصال بین گره ۱ و گره ۲
    (2, 0)  # اتصال بین گره ۲ و گره ۰
]

# رسم خطوط بین گره‌ها
for start, end in members:
    plt.plot([nodes[start, 0], nodes[end, 0]], [nodes[start, 1], nodes[end, 1]], color='blue', linewidth=2)

# تنظیمات نهایی
plt.axis('equal') # حفظ تناسب ابعاد واقعی
plt.grid(True)    # اضافه کردن شبکه راهنما
plt.title("Triangle Truss Plot") # عنوان نمودار

# نمایش نمودار
plt.show()
