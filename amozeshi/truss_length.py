import numpy as np

delta = np.array([3.0, 4.0])

# محاسبه طول عضو با استفاده از نرم بردار
L = np.linalg.norm(delta)

print("Truss Element Length:", L)