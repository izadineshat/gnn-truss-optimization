"""گام ۵ — حل‌کنندهٔ عمومی، بارهای چندگانه، و تولید داده برای GNN.

تا گام ۴ همه‌چیز برای «یک خرپای سه‌عضوی با یک بار» نوشته شده بود. برای آموزش
GNN به هزاران خرپای مختلف با بارهای مختلف نیاز داریم، پس اینجا این کارها را
می‌کنیم:

    ۱) تعمیم  : هر تعداد گره/عضو، هر شکل، هر ترکیب تکیهگاه → یک فراخوانی
    ۲) سرعت   : حذف حلقهٔ دوبلو (برداری‌سازی) تا تولید داده عملی شود
    ۳) چند بار: چند حالت بارگذاری با یک تجزیهٔ ماتریسی همزمان حل شوند
    ۴) ساختار : تولیدکنندهٔ خرپای تصادفی که «با ساخت» بسیار معین است
    ۵) کشف    : یک واقعیت بزرگ که درِ بهینه‌سازی را باز می‌کند
    ۶) داده   : کارخانهٔ تولید داده که ورودی/خروجی خام GNN را روی دیسک می‌ریزد

اجرا:
    python amozeshi/step5_general_solver_and_data.py
"""

import sys
import time
from pathlib import Path

import numpy as np

# کنسول ویندوز پیش‌فرض cp1252 است و فارسی را چاپ نمی‌کند (درسی از گام ۴).
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

SIG_ALLOW = 250e6   # تنش مجاز فولاد (Pa) — محدودیت اصلی بهینه‌سازی
RHO = 7850.0        # چگالی فولاد (kg/m^3)
A_MIN = 1e-5        # کمینهٔ مقطع مجاز (m^2)


# ═══════════════════ ۱. مدل = شیء، نه متغیر سراسری ═══════════════════
class Truss:
    """یک مدل خرپا: هندسه + مقطع + شرایط مرزی.

    چرا کلاس؟ تا اینجا nodes/elements/E/A متغیر سراسری بودند و فقط یک مدل روی
    میز جا می‌شد. حالا هزار مدل متفاوت را کنار هم تولید و حل می‌کنیم.

    نکتهٔ مهم: تکیهگاه «درجه‌آزادی» را قفل می‌کند، نه «گره» را.
        لولایی (pin)   → هر دو جهت قفل → دو درجه‌آزادی
        غلتکی (roller) → یک جهت قفل    → یک درجه‌آزادی
    پس fixed_dofs لیستی از شمارهٔ درجه‌آزادی‌هاست، نه شمارهٔ گره.
    """

    def __init__(self, nodes, elements, E, areas, fixed_dofs):
        self.nodes = np.asarray(nodes, dtype=np.float64)          # (n_nodes, 2)
        self.elements = np.atleast_2d(np.asarray(elements, dtype=np.int64))
        self.fixed_dofs = np.sort(np.atleast_1d(np.asarray(fixed_dofs, dtype=np.int64)))

        self.E = np.asarray(E, dtype=np.float64)
        self.areas = np.asarray(areas, dtype=np.float64)
        if self.E.ndim == 0:
            self.E = np.full(len(self.elements), float(self.E))
        if self.areas.ndim == 0:
            self.areas = np.full(len(self.elements), float(self.areas))

    @property
    def n_nodes(self):
        return len(self.nodes)

    @property
    def n_elem(self):
        return len(self.elements)

    @property
    def n_dof(self):
        return 2 * self.n_nodes

    @property
    def free_dofs(self):
        mask = np.ones(self.n_dof, dtype=bool)
        mask[self.fixed_dofs] = False
        return np.nonzero(mask)[0]

    @property
    def determinacy(self):
        """m + r − 2n. صفر یعنی «بسیار معین» (Statically Determinate)."""
        return self.n_elem + len(self.fixed_dofs) - 2 * self.n_nodes


# ═══════════════════ ۲. هندسه: یک‌جا برای همه اعضا ═══════════════════
def element_geometry(t):
    """طول و بردار تبدیل همهٔ اعضا، بدون هیچ حلقه‌ای.

        L   : (n_elem,)     طول هر عضو
        lam : (n_elem, 4)   [-c, -s, c, s] هر عضو
    """
    i, j = t.elements[:, 0], t.elements[:, 1]
    delta = t.nodes[j] - t.nodes[i]                      # (n_elem, 2)
    L = np.linalg.norm(delta, axis=1)
    c = delta[:, 0] / L
    s = delta[:, 1] / L
    return L, np.column_stack((-c, -s, c, s))


def element_dofs(t):
    """درجه‌آزادی‌های هر عضو: [2i, 2i+1, 2j, 2j+1] → (n_elem, 4)."""
    i, j = t.elements[:, 0], t.elements[:, 1]
    return np.column_stack((2 * i, 2 * i + 1, 2 * j, 2 * j + 1))


# ═══════════════════ ۳. اسمبل: نسخهٔ مرجع و نسخهٔ سریع ═══════════════════
def assemble_reference(t):
    """همان حلقهٔ دوبلوی گام ۴ — کند، ولی «مرجع راستی‌آزمایی» ماست."""
    L, lam = element_geometry(t)
    dofs = element_dofs(t)
    K = np.zeros((t.n_dof, t.n_dof))
    for e in range(t.n_elem):
        k_e = (t.E[e] * t.areas[e] / L[e]) * np.outer(lam[e], lam[e])
        for r, row in enumerate(dofs[e]):
            for c_, col in enumerate(dofs[e]):
                K[row, col] += k_e[r, c_]
    return K


def assemble_vectorized(t):
    """اسمبل برداری: ماتریس همهٔ اعضا یکجا ساخته شود، سپس در K پاشیده شود.

    چرا np.add.at و نه K[rows, cols] += values؟
        چون numpy در شکل دوم با شاخص تکراری فقط یک‌بار می‌نویسد (overwrite) و
        نتیجه غلط می‌شود. این یک تلهٔ کلاسیک است که خیلی‌ها را گول می‌زند.
        عضوهای هم‌گره درایهٔ مشترک دارند، پس حتماً باید «جمع» شود.
    """
    L, lam = element_geometry(t)
    dofs = element_dofs(t)

    coef = t.E * t.areas / L
    # k_e[a,b] = coef * lam[a] * lam[b]  →  (n_elem, 4, 4)
    k_all = coef[:, None, None] * lam[:, :, None] * lam[:, None, :]

    rows = np.repeat(dofs, 4, axis=1).ravel()             # هر ردیف ۴ بار پشت هم
    cols = np.tile(dofs, (1, 4)).ravel()                  # ردیف‌ها ۴ بار تکرار

    K = np.zeros((t.n_dof, t.n_dof))
    np.add.at(K, (rows, cols), k_all.reshape(t.n_elem, 16).ravel())
    return K


# ═══════════════════ ۴. حل، با چند حالت بار همزمان ═══════════════════
def solve(t, loads, K=None):
    """حل K·u = F برای یک یا چند حالت بار.

    loads : (n_dof,) یا (n_dof, n_cases) — هر ستون یک حالت بار.
    خروجی : u (n_dof, n_cases), K, loads (نرمال‌شده به دو بعد)

    چرا چند حالت تقریباً رایگان است؟ چون np.linalg.solve با راست چندستونی،
    تجزیهٔ ماتریس را یک بار انجام می‌دهد و برای همهٔ ستون‌ها به کار می‌برد.
    """
    loads = np.atleast_2d(np.asarray(loads, dtype=np.float64))
    if loads.shape[0] != t.n_dof:
        loads = loads.T
    if K is None:
        K = assemble_vectorized(t)

    free = t.free_dofs
    K_ff = K[np.ix_(free, free)]

    # خوش‌شرطی = سلامت مدل. ماتریس تکین یعنی «مکانیزم»: قفل کم است یا عضوی ناپایدار.
    cond = np.linalg.cond(K_ff)
    if not np.isfinite(cond) or cond > 1e12:
        raise np.linalg.LinAlgError(
            f"ماتریس سختی تکین است (cond = {cond:.2e}).")

    u = np.zeros((t.n_dof, loads.shape[1]))
    u[free] = np.linalg.solve(K_ff, loads[free])
    return u, K, loads


def member_forces(t, u):
    """نیروی محوری اعضا → (n_elem, n_cases).   + کشش  /  − فشار."""
    L, lam = element_geometry(t)
    u_e = u[element_dofs(t)]                        # (n_elem, 4, n_cases)
    elong = np.einsum("ea,ean->en", lam, u_e)        # کشیدگی در راستای محور عضو
    return (t.E * t.areas / L)[:, None] * elong


def member_stress(t, u):
    return member_forces(t, u) / t.areas[:, None]


def reactions(t, K, u, loads):
    """واکنش = (K·u − F) فقط روی درجه‌آزادی‌های مقید؛ آزادها صفر می‌مانند."""
    R = np.zeros_like(u)
    fixed = t.fixed_dofs
    R[fixed] = (K @ u)[fixed] - loads[fixed]
    return R


def nodal_member_forces(t, u, case=0):
    """نیروی memberها روی هر گره، جمع‌شده به‌صورت برداری (برای چک تعادل).

    عضو تحت کشش (N>0) دو سرش را به سمت هم می‌کشد:
        روی گره i  →  +N·d      روی گره j  →  −N·d        (d = واحد از i به j)
    """
    L, lam = element_geometry(t)
    N = member_forces(t, u)[:, case]
    d = lam[:, 2:4]                                  # (n_elem, 2) بردار واحد i→j
    out = np.zeros((t.n_nodes, 2))
    np.add.at(out, t.elements[:, 0], N[:, None] * d)
    np.add.at(out, t.elements[:, 1], -N[:, None] * d)
    return out


def max_node_imbalance(t, u, loads, R, case=0):
    """بزرگ‌ترین عدم‌تعادل در یک گره — باید ~صفر باشد (چک فیزیکی، نه عددی)."""
    balance = (nodal_member_forces(t, u, case)
               + loads[:, case].reshape(-1, 2)
               + R[:, case].reshape(-1, 2))
    return np.abs(balance).max()


# ═══════════════════ ۵. تولیدکنندهٔ خرپای تصادفی «وارن» ═══════════════════
def warren_truss(rng, n_panels=None):
    """یک خرپای وارن تصادفی می‌سازد که «با ساخت» بسیار معین است.

        T1      T2      T3
        /\\    /\\    /\\
       /  \\  /  \\  /  \\
      B0───B1───B2───B3

    چرا تصادفیِ بی‌قاعده نه؟
        چون خرپای بی‌قاعده معمولاً یا «مکانیزم» است یا استاتیك نامعلوم، و
        دیباگش جهنم است. اینجا از قانون «ساخت ساده» (Simple Truss) استفاده
        می‌کنیم که تضمین ریاضی دارد:

            با دو گرهٔ اول شروع کن؛ بعد هر گرهٔ جدید را دقیقاً با
            ۲ عضو غیرهم‌راستا به گره‌های موجود وصل کن
            ⇒  m = 2V − 3      و ساختار هرگز مکانیزم نمی‌شود

        و با ۳ واکنش (لولایی + غلتکی):  m + r = 2V  →  دقیقاً بسیار معین ✅

    برای n پنل:  V = 2n+1 (کف B0..Bn + سقف T1..Tn)، m = 4n−1، r = 3.

    این همان چیزی است که تولید داده می‌خواهد: هر نمونه معتبر است، هیچ‌کدام
    تکین نمی‌شود، و سرعت تولید افت نمی‌کند.
    """
    n = int(rng.integers(3, 7)) if n_panels is None else int(n_panels)
    panel = rng.uniform(1.5, 3.5)
    height = rng.uniform(1.5, 4.0)

    nodes = [[0.0, 0.0], [panel, 0.0]]              # B0 , B1
    elements = [(0, 1)]
    bottom = [0, 1]                                 # ایندکس گره‌های کف، به ترتیب

    def add_node(xy, a, b):
        """گرهٔ جدید با دقیقاً دو عضو به گره‌های موجود اضافه می‌کند."""
        nodes.append([float(xy[0]), float(xy[1])])
        elements.append((len(nodes) - 1, a))
        elements.append((len(nodes) - 1, b))
        return len(nodes) - 1

    for k in range(1, n + 1):
        b_left, b_right = bottom[k - 1], bottom[k]

        # رأس T_k: دقیقاً روی میانهٔ پنل، به دو سر همان پنل وصل می‌شود
        x_apex = 0.5 * (nodes[b_left][0] + nodes[b_right][0])
        apex = add_node([x_apex, height], b_left, b_right)

        if k < n:
            # گره کف بعدی: به گره کف قبلی (کف صاف) و به همین رأس وصل می‌شود
            bottom.append(add_node([nodes[b_right][0] + panel, 0.0], b_right, apex))

    t = Truss(np.array(nodes),
              elements,
              E=200e9,
              areas=rng.uniform(2e-4, 2.0e-3, size=len(elements)),
              fixed_dofs=[0, 1, 2 * bottom[-1] + 1])   # لولایی چپ + غلتکی راست

    # تضمین ریاضی ساخت: m = 2V−3 و m + r = 2V
    if t.determinacy != 0:
        raise AssertionError(f"ساختار معین نیست: m + r − 2V = {t.determinacy}")
    if t.n_elem != 2 * t.n_nodes - 3:
        raise AssertionError(f"ساخت ساده نقض شد: m={t.n_elem} ≠ 2V−3={2 * t.n_nodes - 3}")

    # بار: روی چند رأس میانی، رو به پایین (مقدار تصادفی)
    apex_ids = np.nonzero(t.nodes[:, 1] > 1e-9)[0]
    chosen = rng.permutation(apex_ids)[: max(1, len(apex_ids) - 1)]
    P = float(rng.uniform(-120e3, -40e3))

    loads = np.zeros((t.n_dof, len(chosen)))
    for c, node in enumerate(sorted(chosen)):
        loads[2 * node + 1, c] = P
    return t, loads, np.array(sorted(chosen))


# ═══════════ ۶. واقعیت بزرگی که درِ بهینه‌سازی را باز می‌کند ═══════════
# در سازهٔ «بسیار معین»، نیروی داخلی اعضا فقط از تعادل استاتیک می‌آید و به
# سختی اعضا (E و A) ربطی ندارد. پس:
#       σ_i = N_i / A_i          با N_i ثابت (مستقل از A)
# یعنی تنها اهرم طراحی برای کنترل تنش «مقطع» است، و مسئله به شکل بسته حل می‌شود:
#       A_i* = max( |N_i| / σ_allow , A_min )
# این را در ادامه با عدد ثابت می‌کنیم (چک «★»).


def optimal_areas(N, sigma_allow=SIG_ALLOW, a_min=A_MIN):
    """کمینهٔ مقطع مجاز، در نظر گرفتن «بدترین حالت بار» برای هر عضو."""
    return np.maximum(np.abs(N).max(axis=1) / sigma_allow, a_min)


def uniform_areas(N, sigma_allow=SIG_ALLOW, a_min=A_MIN):
    """روش سنتی محافظه‌کارانه: یک مقطع برای همهٔ اعضا (بر اساس بدترین نیرو)."""
    return np.full(len(N), max(np.abs(N).max() / sigma_allow, a_min))


def weight_of(t, areas, rho=RHO):
    L, _ = element_geometry(t)
    return rho * float(np.sum(areas * L))


# ═══════════════════ ۷. چک‌ها و گزارش ═══════════════════
def header(text):
    print("\n" + "=" * 74)
    print(f"  {text}")
    print("=" * 74)


def check(name, ok, detail=""):
    print(f"  {name:42s} {'OK  ✅' if ok else 'FAIL ❌'}   {detail}")
    return bool(ok)


def run_validations():
    ok = True

    header("بخش ۱ — حل‌کنندهٔ عمومی: نسخهٔ سریع با نسخهٔ مرجع یکی است؟")

    # همان خرپای مثلثی گام ۴، این بار به‌صورت شیء
    tri = Truss(nodes=[[0.0, 0.0], [4.0, 0.0], [2.0, 3.0]],
                elements=[(0, 1), (1, 2), (2, 0)],
                E=200e9, areas=0.01, fixed_dofs=[0, 1, 2, 3])
    F = np.zeros(tri.n_dof); F[5] = -100e3

    K_ref, K_vec = assemble_reference(tri), assemble_vectorized(tri)
    ok &= check("ماتریس K: مرجع == برداری",
                np.allclose(K_ref, K_vec, atol=1e-8),
                f"اختلاف = {np.abs(K_ref - K_vec).max():.2e}")

    u_ref = solve(tri, F, K_ref)[0]
    u_vec, _, _ = solve(tri, F, K_vec)
    ok &= check("جابجایی: هر دو مسیر یکی",
                np.allclose(u_ref, u_vec),
                f"اختلاف = {np.abs(u_ref - u_vec).max():.2e}")

    # رگرسیون: برنگردیم به عددهای شناخته‌شدهٔ گام ۴ (مبادا چیزی خراب شود)
    N_tri = member_forces(tri, u_vec)[:, 0]
    known = np.array([0.0, -100e3 * np.sqrt(13) / 6, -100e3 * np.sqrt(13) / 6])
    ok &= check("نیروها با گام ۴ یکی باشند",
                np.allclose(N_tri, known, rtol=1e-9),
                f"اختلاف = {np.abs(N_tri - known).max():.2e}")

    header("بخش ۲ — بارهای چندگانه و اصل برهم‌نهی")
    loads3 = np.column_stack([F, F * 0.5, -F * 0.25])
    u3, K3, loads3 = solve(tri, loads3)
    u_each = np.column_stack([solve(tri, loads3[:, [c]], K3)[0][:, 0]
                              for c in range(loads3.shape[1])])
    ok &= check("حل همزمان == جمع حل‌های تکی",
                np.allclose(u3, u_each),
                f"اختلاف = {np.abs(u3 - u_each).max():.2e}")
    print(f"      هزینه: یک تجزیه برای {loads3.shape[1]} حالت بار (به‌جای {loads3.shape[1]} تجزیه)")

    u_zero = solve(tri, np.zeros(tri.n_dof))[0]
    ok &= check("بار صفر → جابجایی صفر", np.abs(u_zero).max() < 1e-15)

    header("بخش ۳ — یک مدل تصادفی بزرگ: چک‌های فیزیکی")
    t, loads, loaded = warren_truss(np.random.default_rng(7))
    u, K, loads = solve(t, loads)
    R = reactions(t, K, u, loads)

    print(f"      {t.n_nodes} گره، {t.n_elem} عضو، {t.n_dof} درجه‌آزادی، "
          f"{loads.shape[1]} حالت بار، بار روی گره‌های {[int(v) for v in loaded]}")

    imb = max(max_node_imbalance(t, u, loads, R, c) for c in range(loads.shape[1]))
    ok &= check("تعادل همهٔ گره‌ها در همهٔ حالت‌ها", imb < 1e-6,
                f"حداکثر عدم‌تعادل = {imb:.2e} N")

    g = np.abs(loads.sum(axis=0) + R.sum(axis=0)).max()
    ok &= check("تعادل کل (بار + واکنش = ۰)", g < 1e-6, f"اختلاف = {g:.2e} N")
    ok &= check("شرط ایستایی m + r = 2n", t.determinacy == 0,
                f"m={t.n_elem} r={len(t.fixed_dofs)} 2n={t.n_dof}")

    header("بخش ۴ — سرعت: چرا برداری‌سازی لازم است")
    big, _, _ = warren_truss(np.random.default_rng(1), n_panels=200)
    t0 = time.perf_counter(); assemble_reference(big); dt_ref = time.perf_counter() - t0
    t0 = time.perf_counter(); assemble_vectorized(big); dt_vec = time.perf_counter() - t0
    print(f"      مدل {big.n_elem} عضوی (K = {big.n_dof}×{big.n_dof}):")
    print(f"          حلقه‌ای (مرجع) : {dt_ref * 1000:8.2f} ms")
    print(f"          برداری         : {dt_vec * 1000:8.2f} ms   "
          f"→ {dt_ref / max(dt_vec, 1e-12):.0f}× سریع‌تر")
    ok &= check("برداری دست‌کم ۲ برابر سریع‌تر", dt_vec * 2 < dt_ref)

    header("بخش ۵ — ★ کشف اصلی: نیروها مستقل از مقطع‌اند ★")
    t2, loads2, _ = warren_truss(np.random.default_rng(20))
    u2, _, loads2 = solve(t2, loads2)
    N_base = member_forces(t2, u2)

    t3 = Truss(t2.nodes, t2.elements, E=t2.E,
               areas=np.random.default_rng(99).uniform(2e-4, 2e-3, size=t2.n_elem),
               fixed_dofs=t2.fixed_dofs)
    u3b, _, _ = solve(t3, loads2)
    N_changed = member_forces(t3, u3b)

    rel = np.abs(N_base - N_changed).max() / np.abs(N_base).max()
    ok &= check("★ مقطع‌ها عوض شوند، نیروها عوض نشوند ★", rel < 1e-9,
                f"اختلاف نسبی = {rel:.2e}")
    du = np.abs(u2 - u3b).max()
    print(f"\n      ولی جابجایی‌ها عوض می‌شوند (حداکثر اختلاف = {du * 1000:.4f} mm) —")
    print("      پس GNN برای پیش‌بینی u حتماً باید مقطع را ببیند؛ برای N نه.")
    print("      💡 این تفاوت، همان چیزی است که مسئلهٔ بهینه‌سازی را 'بسته' می‌کند.")

    return ok


def show_optimization():
    header("بخش ۶ — اولین بهینه‌سازی واقعی (تحلیلی، بدون الگوریتم)")
    t, loads, loaded = warren_truss(np.random.default_rng(42))
    u, K, loads = solve(t, loads)
    N = member_forces(t, u)

    A_opt = optimal_areas(N)
    A_uni = uniform_areas(N)
    W_opt = weight_of(t, A_opt)
    W_uni = weight_of(t, A_uni)
    saving = (1 - W_opt / W_uni) * 100

    print(f"  مدل: {t.n_nodes} گره، {t.n_elem} عضو، {loads.shape[1]} حالت بار")
    print(f"  حد تنش مجاز: {SIG_ALLOW / 1e6:.0f} MPa\n")
    print(f"  روش سنتی (یک مقطع برای همه)  : A = {A_uni[0] * 1e4:6.2f} cm²  "
          f"→  وزن = {W_uni / 1000:7.3f} ton")
    print(f"  روش کمینهٔ وزن (مقطع بهینه)  : ΣA= {A_opt.sum() * 1e4:6.2f} cm²  "
          f"→  وزن = {W_opt / 1000:7.3f} ton")
    print(f"  ➜ صرفه‌جویی: {saving:.1f}%   فقط با استاتیك، بدون هیچ جست‌وجویی!")

    # با مقطع‌های بهینه دوباره حل کنیم و مطمئن شویم هیچ‌چیز نقض نشده
    t_opt = Truss(t.nodes, t.elements, E=t.E, areas=A_opt, fixed_dofs=t.fixed_dofs)
    u_opt, K_opt, loads_opt = solve(t_opt, loads)
    R_opt = reactions(t_opt, K_opt, u_opt, loads_opt)
    sig = member_stress(t_opt, u_opt)

    ok = True
    ok &= check("هیچ تنشی از حد مجاز رد نشود", sig.max() <= SIG_ALLOW * (1 + 1e-9),
                f"max|σ| = {sig.max() / 1e6:.2f} MPa")
    imb = max(max_node_imbalance(t_opt, u_opt, loads_opt, R_opt, c)
              for c in range(loads_opt.shape[1]))
    ok &= check("تعادل با مقطع‌های بهینه", imb < 1e-6, f"عدم‌تعادل = {imb:.2e} N")

    n_active = int(np.sum(np.abs(sig).max(axis=1) > SIG_ALLOW * 0.999))
    print(f"  اعضای «رسیده به حد مجاز» (فعال): {n_active} از {t_opt.n_elem}")
    print(f"  جابجایی کل با مقطع بهینه        : {np.abs(u_opt).max() * 1000:.3f} mm")

    order = np.argsort(-A_opt)[:5]
    print("\n  ۵ عضو قطورتر (همان‌هایی که GNN باید بفهمد مهم‌اند):")
    for e in order:
        i, j = t.elements[e]
        kind = "کشش" if N[e].max() == abs(N[e]).max() else "فشار"
        print(f"      عضو {i:3d}–{j:3d}   A = {A_opt[e] * 1e4:5.2f} cm²   "
              f"|N|max = {abs(N[e]).max() / 1e3:7.2f} kN   ({kind})")
    return ok


def build_dataset(n_samples=60, seed=0, out_dir="amozeshi/dataset"):
    header("بخش ۷ — کارخانهٔ تولید داده (غذای GNN)")
    rng = np.random.default_rng(seed)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    records = []
    t0 = time.perf_counter()
    for _ in range(n_samples):
        t, loads, loaded = warren_truss(rng)
        u, K, loads = solve(t, loads)
        R = reactions(t, K, u, loads)
        L, _ = element_geometry(t)

        records.append({
            # ── ورودی خام، در قالب گراف ─────────────────────────
            "node_coord": t.nodes.astype(np.float32),                       # (V, 2)
            "node_fix_x": np.isin(2 * np.arange(t.n_nodes), t.fixed_dofs).astype(np.float32),
            "node_fix_y": np.isin(2 * np.arange(t.n_nodes) + 1, t.fixed_dofs).astype(np.float32),
            "node_load": loads.sum(axis=1).reshape(-1, 2).astype(np.float32),
            "edge_index": t.elements.T.astype(np.int64),                     # (2, E)
            "edge_area": t.areas.astype(np.float32),
            "edge_len": L.astype(np.float32),
            # ── برچسب‌ها (ground truth که FEM حساب کرده) ────────
            "u": u.astype(np.float32),
            "force": member_forces(t, u).astype(np.float32),
            "stress": member_stress(t, u).astype(np.float32),
            "reac": R.astype(np.float32),
        })

    dt = time.perf_counter() - t0
    path = out / f"trusses_{len(records)}.npz"

    # تعداد گره/عضو در نمونه‌ها فرق می‌کند، پس نمی‌توان آنها را در یک آرایهٔ
    # معمولی جای داد. تلهٔ کلاسیک numpy: np.array(list_of_arrays, dtype=object)
    # وقتی شکل‌ها اتفاقی برابر باشند، تلاش به «پخش» (broadcast) می‌کند و می‌شکند.
    # راه درست و قطعی: ساخت جعبهٔ خالی و پر کردنش یکی‌یکی.
    keys = list(records[0])
    packed = {}
    for k in keys:
        box = np.empty(len(records), dtype=object)
        for idx, r in enumerate(records):
            box[idx] = r[k]
        packed[k] = box
    np.savez_compressed(path, **packed)

    nv = np.array([r["node_coord"].shape[0] for r in records])
    ne = np.array([r["edge_index"].shape[1] for r in records])
    nc = np.array([r["u"].shape[1] for r in records])
    smax = np.array([np.abs(r["stress"]).max() for r in records])

    print(f"  نمونه‌ها: {len(records)}   زمان: {dt:.2f} s  →  "
          f"{dt / len(records) * 1000:.1f} ms برای هر نمونه")
    print(f"  فایل   : {path}  ({path.stat().st_size / 1024:.0f} KiB)")
    print(f"\n  تنوع داده (کیفیت = تنوع):")
    print(f"      گره‌ها    : {nv.min()}–{nv.max()}   (میانگین {nv.mean():.1f})")
    print(f"      اعضا     : {ne.min()}–{ne.max()}")
    print(f"      حالت بار : {nc.min()}–{nc.max()}")
    print(f"      |σ|max   : {smax.min() / 1e6:.1f}–{smax.max() / 1e6:.1f} MPa")
    print(f"\n  مقیاس‌پذیری: ۱۰٬۰۰۰ نمونه ≈ {dt / len(records) * 10000 / 60:.1f} دقیقه")

    # خواندن دوبارهٔ فایل: ثابت کنیم داده سالم و برگشت‌پذیر است
    z = np.load(path, allow_pickle=True)
    first = z["node_coord"][0]
    ok_reload = np.allclose(first, records[0]["node_coord"])
    print(f"\n  چک: فایل را دوباره بخوان → مختصات نمونهٔ ۱ برگشت؟ "
          f"{'بله ✅' if ok_reload else 'نه ❌'}")
    print(f"  keys موجود در فایل: {list(z.keys())}")

    print("\n  💡 قالب ذخیره همان چیزی است که گام ۷ لازم دارد:")
    print("      edge_index (2,E) + ویژگی گره + ویژگی یال  →  u / force / stress")
    return path, ok_reload


def main():
    ok = run_validations()
    ok &= show_optimization()
    path, ok_reload = build_dataset()

    header("جمع‌بندی گام ۵")
    print("  اضافه شد : مدل شیء‌محور · اسمبل برداری · چند حالت بار در یک حل ·")
    print("             چک تعادل · تولیدکنندهٔ «ساخت ساده» · داده روی دیسک.")
    print("  کشف شد   : در سازهٔ معین N مستقل از A است  →  σ = N/A  →")
    print("             کمینهٔ وزن تحلیلی است، پس بهینه‌سازی «بسته» می‌شود.")
    print("             (برای u باید مقطع را ببینیم؛ برای N لازم نیست.)")
    print("\n  وضعیت   : " + ("✅ همهٔ چک‌ها پاس شد → می‌توانیم برویم گام ۶ (گراف)"
                                if ok and ok_reload else
                                "❌ جایی می‌لنگد — اول این را درست کن"))


if __name__ == "__main__":
    main()
