import matplotlib.pyplot as plt
import numpy as np

#مختصات اولیه گره ها
node1_init = np.array([0, 0])
node2_init = np.array([4, 3])

# جابه جایی گره‌ها برای نمایش تغییرات
u = np.array([0.0, 0.0, 0.5, -0.3])  # جابه جایی گره‌ها

#مختصات تعغیر یافته گره‌ها
node1_deformed = node1_init + u[0:2]
node2_deformed = node2_init + u[2:4]    

plt.figure(figsize=(6, 5))

#رسم عضو اولیه (خط چین خاکستری)
plt.plot([node1_init[0], node2_init[0]], [node1_init[1], node2_init[1]], 'k--', label='Initial Member', linewidth=2)
plt.scatter([node1_init[0], node2_init[0]], [node1_init[1], node2_init[1]], color='blue', label='Initial Nodes')

#رسم عضو تغییر یافته (خط قرمز)
plt.plot([node1_deformed[0], node2_deformed[0]], [node1_deformed[1], node2_deformed[1]], 'r-', label='Deformed Member', linewidth=2)
plt.scatter([node1_deformed[0], node2_deformed[0]], [node1_deformed[1], node2_deformed[1]], color='red', label='Deformed Nodes')

plt.title('Truss Member Deformation')
plt.xlabel('X Coordinate (m)')
plt.ylabel('Y Coordinate (m)')
plt.grid(True)
plt.legend()
plt.show()