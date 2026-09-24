import numpy as np
import matplotlib.pyplot as plt

def solve_truss():
    # ۱. تعریف مشخصات هندسی و متریال
    nodes = np.array([
        [0.0, 0.0],  # گره ۰
        [4.0, 0.0],  # گره ۱
        [2.0, 3.0]   # گره ۲
    ])
    
    # بررسی ابعاد آرایه گره‌ها پس از بارگذاری در حافظه
    # خروجی مورد انتظار: (۳، ۲) یعنی ۳ گره و ۲ ویژگی مختصات (x, y)
    print("Nodes array:")
    print(nodes)
    print("Shape of nodes:", nodes.shape)
    print("dtype of nodes:", nodes.dtype)
    
    # اتصالات (مبدأ، مقصد)
    elements = [
        (0, 1),
        (1, 2),
        (2, 0)
    ]
    
    E = 200e9  # Pa (فولاد)
    A = 0.01   # m^2 (مقطع)
    
    num_nodes = len(nodes)
    num_dofs = 2 * num_nodes
    K_global = np.zeros((num_dofs, num_dofs))
    
    # ۲. اسمبل کردن ماتریس سختی کل
    for i, j in elements:
        # مختصات گره‌ها
        p1 = nodes[i]
        p2 = nodes[j]
        
        # طول و جهت عضو
        L = np.linalg.norm(p2 - p1)
        c = (p2[0] - p1[0]) / L
        s = (p2[1] - p1[1]) / L
        
        # ماتریس انتقال موضعی به کلی برای عضو خرپا
        lambda_vec = np.array([-c, -s, c, s])
        k_element = (E * A / L) * np.outer(lambda_vec, lambda_vec)
        
        # درجات آزادی مربوط به گره i و j
        dofs = [2*i, 2*i+1, 2*j, 2*j+1]
        
        # جایگذاری در ماتریس کل
        for row_idx, row in enumerate(dofs):
            for col_idx, col in enumerate(dofs):
                K_global[row, col] += k_element[row_idx, col_idx]
                
    # ۳. تعریف بارگذاری و شرایط مرزی
    # فرض: گره ۰ و ۱ ثابت (تکیه‌گاه لولایی)
    # بار متمرکز به مقدار 100kN به سمت پایین روی گره ۲
    F = np.zeros(num_dofs)
    F[2*2 + 1] = -100000  # نیروی ۱۰۰ کیلونیوتون در راستای y منفی روی گره ۲
    
    # درجات آزادی آزاد (آنهایی که مقید نیستند)
    # گره ۰ (dof 0,1) و گره ۱ (dof 2,3) مقید هستند.
    # فقط گره ۲ (dof 4,5) آزاد است.
    free_dofs = [4, 5]
    
    # ۴. حل سیستم معادلات برای درجات آزادی آزاد
    K_free = K_global[np.ix_(free_dofs, free_dofs)]
    F_free = F[free_dofs]
    
    u_free = np.linalg.solve(K_free, F_free)
    
    # بردار جابجایی کل
    u_global = np.zeros(num_dofs)
    u_global[free_dofs] = u_free
    
    print("Displacements at node 2 (u_x, u_y):", u_free)
    
    # ۵. نمایش نتایج
    # مختصات جدید گره‌ها
    new_nodes = nodes + u_global.reshape(num_nodes, 2)
    
    plt.figure(figsize=(10, 6))
    
    # رسم سازه اولیه
    for i, j in elements:
        plt.plot([nodes[i,0], nodes[j,0]], [nodes[i,1], nodes[j,1]], 'k--', alpha=0.3, label='Original' if i==0 and j==1 else "")
        
    # رسم سازه تغییر شکل یافته (با بزرگنمایی برای وضوح)
    scale = 500 # ضریب بزرگنمایی برای نمایش جابجایی
    scaled_nodes = nodes + u_global.reshape(num_nodes, 2) * scale
    
    for i, j in elements:
        plt.plot([scaled_nodes[i,0], scaled_nodes[j,0]], [scaled_nodes[i,1], scaled_nodes[j,1]], 'r-o', linewidth=2, label='Deformed (scaled)' if i==0 and j==1 else "")
        
    plt.title("Truss Analysis - Displacement Visualization")
    plt.xlabel("X (m)")
    plt.ylabel("Y (m)")
    plt.legend()
    plt.grid(True)
    plt.axis('equal')
    plt.show()

if __name__ == "__main__":
    solve_truss()
