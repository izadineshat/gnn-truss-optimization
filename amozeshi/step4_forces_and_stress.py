"""گام ۴ — از جابجایی به نیرو و تنش.

داستان این فایل در سه جمله:
    ۱. تا الان فقط «جابجایی گره‌ها» را حساب می‌کردیم (u).
    ۲. اینجا همان جواب را به «نیروی داخلی هر عضو» و «تنش» ترجمه می‌کنیم.
    ۳. بعد جواب را با محاسبهٔ دستی روی کاغذ چک می‌کنیم تا مطمئن شویم اشتباه نیست.

چرا این گام برای پروژه حیاتی است؟
    چون در بهینه‌سازی، محدودیت اصلی «تنش» است:
        «وزن را کم کن، ولی نگذار تنش از حد مجاز رد شود.»
    پس بدون تنش، اصلاً نمی‌توانیم بگوییم یک طرح خوب است یا بد.

اجرا:
    python amozeshi/step4_forces_and_stress.py
"""

import sys
import numpy as np
import matplotlib.pyplot as plt

# کنسول ویندوز به‌صورت پیش‌فرض با کدینگ cp1252 کار می‌کند و حروف فارسی را
# نمی‌تواند چاپ کند (خطای UnicodeEncodeError). این دو خط استream را به UTF-8
# سوییچ می‌کنند تا فارسی‌ها درست دیده شوند.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


# ─────────────────────────── ۱. تعریف مدل ───────────────────────────
# سه گره، سه عضو — همان خرپای مثلثی همیشگی (فایل truss_analysis.py).
NODES = np.array([
    [0.0, 0.0],   # گره ۰ — تکیهگاه (مقید)
    [4.0, 0.0],   # گره ۱ — تکیهگاه (مقید)
    [2.0, 3.0],   # گره ۲ — آزاد، محل اعمال بار
])
ELEMENTS = [(0, 1), (1, 2), (2, 0)]   # (مبدأ، مقصد) هر عضو

E = 200e9      # مدول الاستیسیته فولاد (Pa)
A = 0.01       # سطح مقطع همه اعضا (m^2)
P = 100e3      # مقدار بار (N) که رو به پایین به گره ۲ وارد می‌شود
FIXED_NODES = [0, 1]


# ─────────────────── ۲. هندسهٔ هر عضو (طول و جهت) ───────────────────
def element_geometry(nodes, i, j):
    """طول و جهت (کسینوس/سینوس) یک عضو را برمی‌گرداند.

    جهت همیشه «از i به سمت j» است. دقت کن که (c, s) یک بردار واحد است:
    یعنی c^2 + s^2 = 1. این فقط نسبت اضلاع مثلث است، نه فاصله.
    """
    delta = nodes[j] - nodes[i]          # مثلاً برای عضو ۰–۱: [4-0, 0-0] = [4, 0]
    L = np.linalg.norm(delta)            # طول عضو (قضیهٔ فیثاغورس)
    c, s = delta / L                     # بردار واحد جهت
    return L, c, s


# ─────────────────── ۳. اسمبل ماتریس سختی کل ───────────────────
def assemble_stiffness(nodes, elements, E, A):
    """ماتریس سختی کل K را از روی تک‌تک اعضا می‌سازد.

    نکتهٔ آموزشی: هر عضو فقط روی ۴ سطر/ستون خودش اثر می‌گذارد
    (درجه‌آزادی‌های دو سرش). همین باعث می‌شود K توپر نماند و
    در گام ۵ همین حلقهٔ دوبلو را برداری و سریع می‌کنیم.
    """
    n_dof = 2 * len(nodes)
    K = np.zeros((n_dof, n_dof))

    for i, j in elements:
        L, c, s = element_geometry(nodes, i, j)

        # بردار تبدیل: جابجایی‌های x,y گره‌ها را به «کشیدگی طولی» عضو نگاشت می‌کند
        lam = np.array([-c, -s, c, s])

        # ماتریس سختی عضو در مختصات کلی (۴×۴)
        k_element = (E * A / L) * np.outer(lam, lam)

        dofs = [2 * i, 2 * i + 1, 2 * j, 2 * j + 1]
        for row_idx, row in enumerate(dofs):
            for col_idx, col in enumerate(dofs):
                K[row, col] += k_element[row_idx, col_idx]

    return K


# ─────────────── ۴. حل K·u = F (فقط درجه‌آزادی‌های آزاد) ───────────────
def solve_displacements(K, F, fixed_nodes):
    """سیستم را با حذف درجه‌آزادی‌های مقید حل می‌کند و u کامل را می‌دهد."""
    n_dof = K.shape[0]

    # شمارهٔ درجه‌آزادی‌های مقید و آزاد
    fixed_dofs = [d for n in fixed_nodes for d in (2 * n, 2 * n + 1)]
    free_dofs = [d for d in range(n_dof) if d not in fixed_dofs]

    # فقط بخش آزادِ ماتریس را حل می‌کنیم (تکنیک «حذف سطر و ستون»)
    K_free = K[np.ix_(free_dofs, free_dofs)]
    F_free = F[free_dofs]
    u_free = np.linalg.solve(K_free, F_free)

    u = np.zeros(n_dof)
    u[free_dofs] = u_free
    return u, np.array(fixed_dofs), np.array(free_dofs)


# ───────────── ۵. ★ نیروی داخلی و تنش هر عضو (قلب گام ۴) ★ ─────────────
def member_forces_and_stress(nodes, elements, E, A, u):
    """نیروی محوری و تنش هر عضو را از روی جابجایی‌ها حساب می‌کند.

    منطق در سه خط:
        ۱) اختلاف جابجایی دو سر عضو را می‌گیریم.
        ۲) آن را در جهت عضو «اسکالر ضرب» می‌کنیم → فقط جزء کشیدگی/فشار کوتاه شدن.
        ۳) کشیدگی × سختی عضو (EA/L) = نیروی محوری.

    علامت:
        N > 0  →  کشش   (عضو مثل کش لاستیکی کشیده شده)
        N < 0  →  فشار  (عضو مثل ستون زیر وزن فشرده شده)
    """
    n_force = np.zeros(len(elements))
    n_stress = np.zeros(len(elements))

    for idx, (i, j) in enumerate(elements):
        L, c, s = element_geometry(nodes, i, j)

        du = u[[2 * j, 2 * j + 1]] - u[[2 * i, 2 * i + 1]]   # اختلاف جابجایی دو سر
        elongation = du @ np.array([c, s])                    # کشیدگی در راستای محور

        n_force[idx] = (E * A / L) * elongation               # N = (EA/L) · Δ
        n_stress[idx] = n_force[idx] / A                      # σ = N / A

    return n_force, n_stress


# ───────────── ۶. واکنش تکیه‌گاه‌ها ─────────────
def support_reactions(K, u, F, fixed_nodes):
    """نیروهایی که تکیه‌گاه‌ها به سازه وارد می‌کنند.

    ایده: اگر جابجایی را در کل K ضرب کنیم، نیروی «داخلی» همه گره‌ها را داریم.
    در گره‌های آزاد این نیرو با بار خارجی برابر است (پس تفاضل صفر می‌شود).
    در گره‌های مقید بار خارجی نداریم، پس همان تفاضل = واکنش تکیه‌گاه است.
    """
    F_internal = K @ u
    R = np.zeros_like(F)
    for n in fixed_nodes:
        for d in (2 * n, 2 * n + 1):
            R[d] = F_internal[d] - F[d]
    return R


# ───────── ۷. گزارش و اعتبارسنجی (چک کردن جواب با کاغذ و قلم) ─────────
def node_equilibrium_residual(nodes, elements, F, R, N):
    """برای هر گره: جمع نیروی اعضا + بار خارجی + واکنش باید صفر شود."""
    residual = np.zeros_like(nodes)
    for idx, (i, j) in enumerate(elements):
        _, c, s = element_geometry(nodes, i, j)
        # کشش، هر دو سر را به سمت یکدیگر می‌کشد
        residual[i] += N[idx] * np.array([c, s])
        residual[j] += N[idx] * np.array([-c, -s])
    residual += F.reshape(-1, 2) + R.reshape(-1, 2)
    return residual


def report(nodes, elements, u, N, stress, R, F):
    L_arr = np.array([element_geometry(nodes, i, j)[0] for i, j in elements])

    print("=" * 74)
    print("گزارش گام ۴ — تحلیل کامل خرپا")
    print("=" * 74)

    print("\n[۱] جابجایی گره‌ها (متر):")
    for n, (ux, uy) in enumerate(u.reshape(-1, 2)):
        tag = "تکیهگاه — مقید" if n in FIXED_NODES else "آزاد"
        print(f"    گره {n}:  ux = {ux:+.6e}   uy = {uy:+.6e}   ({tag})")

    print("\n[۲] نیروی داخلی و تنش اعضا:")
    print("    عضو   طول(m)      نیرو(N)        نیرو(kN)    تنش(MPa)    حالت")
    print("    " + "-" * 66)
    for idx, (i, j) in enumerate(elements):
        state = "کشش  (+)" if N[idx] > 1e-6 else ("فشار (-)" if N[idx] < -1e-6 else "صفر   (0)")
        print(f"    {i}–{j}    {L_arr[idx]:6.3f}   {N[idx]:+12.1f}   {N[idx]/1e3:+9.3f}   "
              f"{stress[idx]/1e6:+9.3f}   {state}")

    print("\n[۳] واکنش تکیه‌گاه‌ها (N):")
    for n in FIXED_NODES:
        print(f"    گره {n}:  Rx = {R[2*n]:+12.1f}   Ry = {R[2*n+1]:+12.1f}")

    # تعادل کلی: جمع برداری بارها + واکنش‌ها باید صفر شود
    total = F + R
    print("\n[۴] بررسی تعادل کل سازه:")
    print(f"    جمع نیروی افقی = {total[0::2].sum():+.6f} N   (باید ۰ باشد)")
    print(f"    جمع نیروی عمودی = {total[1::2].sum():+.6f} N   (باید ۰ باشد)")

    # تعادل هر گره
    res = node_equilibrium_residual(nodes, elements, F, R, N)
    print(f"    بزرگ‌ترین عدم‌تعادل در یک گره = {np.abs(res).max():.6e} N")

    return L_arr


def verify_against_hand_calculation(nodes, elements, u, N, stress, R):
    """جواب عددی را با جواب کاغذی مقایسه می‌کند.

    محاسبهٔ دستی روی کاغذ (همین خرپای متقارن، بار عمودی روی گره ۲):

      ۱) طول هر عضو شیب‌دار = sqrt(2² + 3²) = sqrt(13)

      ۲) عضو کف (۰–۱): هر دو سرش مقید است، پس کشیدگی = صفر  →  N₀₁ = ۰
         (عضو صفری — force-free member)

      ۳) تعادل گره ۲ در راستای y، با دو نیروی برابر N (به‌خاطر قرینگی):
             2 · N · (3/sqrt13) − P = 0     →     N = P·sqrt13 / 6
         علامت: این نیرو عضو را «فشرده» می‌کند، پس منفی:   N = −P·sqrt13/6

      ۴) تعادل گره ۲ در راستای x:  دو مولفهٔ افقی برابر و مخالف‌اند → خودبه‌خود صفر

      ۵) واکنش‌ها از تعادل گره ۰ و ۱:
             Ry₀ = Ry₁ = P/2          (نصف بار روی هر تکیهگاه، به‌خاطر قرینگی)
             Rx₀ = +P/3 ,  Rx₁ = −P/3  (یکدیگر را خنثی می‌کنند)

      ۶) جابجایی عمودی گره ۲:
             stiffness عمودی = 2 · (EA/L) · s²  ,  s = 3/sqrt13  →  s² = 9/13
             uy = −P / [2 · (EA/L) · 9/13]

      اعداد نهایی (با P = ۱۰۰kN، E = ۲۰۰GPa، A = ۰٫۰۱):
             N = −۶۰٬۰۹۲٫۵ N  ≈ −۶۰٫۰۹ kN   (فشار)
             σ = −۶٫۰۱ MPa
             uy(گره ۲) = −۱٫۳۰۲e-۴ m  ≈ −۰٫۱۳ mm

    نکته: هر دو تکیهگاه در x هم مقید گرفته شده‌اند (ایده‌آل‌سازی). به همین
    دلیل دو سر عضو کف هیچ حرکتی ندارند و آن عضو «صفری» می‌شود.
    """
    L_slant = np.sqrt(2**2 + 3**2)

    N_hand = np.array([
        0.0,                       # عضو کف: صفری
        -P * L_slant / 6.0,        # عضو ۱–۲
        -P * L_slant / 6.0,        # عضو ۲–۰
    ])
    stress_hand = N_hand / A
    R_hand = np.array([P / 3, P / 2, -P / 3, P / 2, 0, 0])   # N
    uy_hand = -P / (2 * (E * A / L_slant) * (9 / 13))

    print("\n" + "=" * 74)
    print("اعتبارسنجی: جواب FEM در برابر محاسبهٔ دستی")
    print("=" * 74)

    checks = [
        ("نیروی اعضا (N)",        N, N_hand),
        ("تنش اعضا (Pa)",         stress, stress_hand),
        ("واکنش‌ها (N)",          R, R_hand),
        ("جابجایی گره ۲ (m)",     u[[4, 5]], np.array([0.0, uy_hand])),
    ]

    all_ok = True
    for name, fem, hand in checks:
        diff = np.abs(fem - hand).max()
        scale = max(np.abs(hand).max(), 1.0)
        rel = diff / scale
        ok = rel < 1e-6
        all_ok &= ok
        flag = "OK  ✅" if ok else "FAIL ❌"
        print(f"  {name:22s} حداکثر اختلاف نسبی = {rel:.2e}   {flag}")

    print("-" * 74)
    print("  نتیجه:", "همه‌چیز می‌خواند — کد درست است ✅" if all_ok
          else "جواب‌ها نمی‌خواند! باید دیباگ کنیم ❌")
    print("=" * 74)
    return all_ok


# ───────── ۸. رسم حرفه‌ای: رنگ = وضعیت عضو ─────────
def plot_results(nodes, elements, u, N, L_arr, scale=400, save_path=None):
    """سازه را با رنگِ نیروی داخلی رسم می‌کند.

    قرمز = فشار، آبی = کشش. ضخامت خط هم متناسب با اندازهٔ نیروست.
    این همان نقشه‌ای است که در بهینه‌سازی به آن نگاه می‌کنیم.
    """
    fig, ax = plt.subplots(figsize=(11, 7.5))

    deformed = nodes + u.reshape(-1, 2) * scale

    # سازهٔ اولیه
    for (i, j) in elements:
        ax.plot(nodes[[i, j], 0], nodes[[i, j], 1], "k--", lw=1, alpha=0.3)

    # سازهٔ تغییرشکل‌یافته، رنگ‌شده بر اساس علامت نیرو
    max_abs = max(np.abs(N).max(), 1.0)
    for idx, (i, j) in enumerate(elements):
        color = "crimson" if N[idx] < 0 else ("tab:blue" if N[idx] > 0 else "0.5")
        width = 1.5 + 4.5 * abs(N[idx]) / max_abs
        ax.plot(deformed[[i, j], 0], deformed[[i, j], 1],
                color=color, lw=width, solid_capstyle="round", zorder=2)

        # برچسب نیرو در وسط عضو
        mid = deformed[[i, j]].mean(axis=0)
        ax.annotate(f"{N[idx] / 1e3:+.1f} kN", xy=mid, fontsize=10,
                    ha="center", va="center",
                    xytext=(mid[0], mid[1] + 0.22),
                    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=color, alpha=0.85))

    # گره‌ها
    ax.scatter(nodes[:, 0], nodes[:, 1], s=90, c="k", zorder=4, label="Nodes")

    # تکیهگاه‌ها (مثلث)
    for n in FIXED_NODES:
        ax.scatter([nodes[n, 0]], [nodes[n, 1] - 0.25], marker="^",
                   s=420, c="0.35", zorder=3)

    # پیکان بار
    ax.annotate("", xy=(nodes[2, 0], nodes[2, 1] - 0.75),
                xytext=(nodes[2, 0], nodes[2, 1] + 0.15),
                arrowprops=dict(arrowstyle="-|>", lw=2.5, color="darkorange"))
    ax.text(nodes[2, 0] + 0.12, nodes[2, 1] - 0.45, f"P = {P / 1e3:.0f} kN",
            fontsize=11, color="darkorange")

    # پیکان جابجایی
    ax.annotate("", xy=deformed[2], xytext=nodes[2],
                arrowprops=dict(arrowstyle="-|>", lw=2, color="green"))

    from matplotlib.lines import Line2D
    legend_items = [
        Line2D([], [], color="k", ls="--", lw=1, alpha=0.4, label="Original"),
        Line2D([], [], color="crimson", lw=4, label="Compression"),
        Line2D([], [], color="tab:blue", lw=4, label="Tension"),
        Line2D([], [], marker="^", ls="", color="0.35", ms=12, label="Support"),
        Line2D([], [], color="green", lw=2, label=f"Displacement x{scale}"),
    ]
    ax.legend(handles=legend_items, loc="lower right", fontsize=9)

    ax.set_title("Step 4 — Member Forces & Stress Map")
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.set_ylim(-0.9, 4.2)
    ax.axis("equal")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=140)
        print(f"\nنقشهٔ نیرو ذخیره شد: {save_path}")
    else:
        plt.show()


# ───────────────────────── اجرا ─────────────────────────
def main(save_path=None):
    # بار خارجی: فقط مولفهٔ y گره ۲، رو به پایین
    F = np.zeros(2 * len(NODES))
    F[2 * 2 + 1] = -P

    K = assemble_stiffness(NODES, ELEMENTS, E, A)
    u, fixed_dofs, free_dofs = solve_displacements(K, F, FIXED_NODES)
    N, stress = member_forces_and_stress(NODES, ELEMENTS, E, A, u)
    R = support_reactions(K, u, F, FIXED_NODES)

    print(f"درجه‌آزادی‌ها: {K.shape[0]}   (مقید: {fixed_dofs}  |  آزاد: {free_dofs})")
    L_arr = report(NODES, ELEMENTS, u, N, stress, R, F)
    verify_against_hand_calculation(NODES, ELEMENTS, u, N, stress, R)
    plot_results(NODES, ELEMENTS, u, N, L_arr, save_path=save_path)


if __name__ == "__main__":
    # اگر بخواهی به‌جای پنجرهٔ گراف، فقط عکس ذخیره شود:
    #     set TRUSS_SAVE_PNG=out.png  &&  python amozeshi/step4_forces_and_stress.py
    import os
    main(save_path=os.environ.get("TRUSS_SAVE_PNG"))
