"""
Emissions and cost of tension and compression chords
(Python port of the Mathcad worksheet "kfm Research, ETH Zürich", based on lecture notes PM / kfm)

Last-Verformungs-Verhalten N(u) von Zug-/Druckgurten der Länge L0 = 1 m.
Die Querschnittsfläche ergibt sich aus einem fixen Budget von 100 kgCO2 (bzw. 100 CHF):

    A = 100 / (e * L0)          e  in kgCO2/m3   (bzw. c in CHF/m3)

Vorzeichen: u > 0 Verlängerung (Zug), u < 0 Verkürzung (Druck).
Einheiten intern: SI (N, m, Pa). Ausgabe: N in MN, u in mm.

Enthalten ist auch der umschnürte Beton (confined concrete, S. 15/16, nur Druck).
"""

import numpy as np
import matplotlib.pyplot as plt

MPa, GPa = 1e6, 1e9
mm = 1e-3
g = 9.81  # m/s2

L0 = 1.0  # m
BUDGET = 100.0  # kgCO2 bzw. CHF

# =============================================================================
# 1) Materialeigenschaften (S. 1-2)
# =============================================================================
# Beton
f_cd = 30 / 1.5 * MPa
f_ctm = 3 * MPa
E_c = 35 * GPa
eps_c1d = -0.002
eps_c2d = -0.0035   # SIA 262:2025, Tabelle 8 (Worksheet: -0.003)

# Betonstahl
f_sd = 500 / 1.15 * MPa
f_su = 540 / 1.15 * MPa
E_s = 200 * GPa
eps_su = 0.05

# Spannstahl
f_pd = 0.85 * 1860 / 1.15 * MPa
f_pud = 1860 / 1.15 * MPa
E_p = 200 * GPa
eps_pu = 0.02

# Baustahl
f_ad = 355 / 1.05 * MPa
f_au = 510 / 1.05 * MPa
E_a = 200 * GPa
eps_au = 0.1

# Brettschichtholz BSH GL24h
f_ttd = 0.9 * 12 * MPa
f_tcd = 14.5 * MPa
E_t = 11 * GPa

# Vollholz C24
f_ttd24 = 0.9 * 8.5 * MPa
f_tcd24 = 12.4 * MPa
E_t24 = 11 * GPa

# UHPFRC (2052, UA)
f_utd = 0.835 * 12 / 1.5 * MPa
f_ued = 0.835 * 10 / 1.5 * MPa
f_ucd = (140 - 8) / 1.5 * MPa
E_u = 50 * GPa
eps_uu = 0.002

# Kohlefaser (s = short term, l = long term)
f_cfs = 2100 * MPa
f_cfl = 840 * MPa
E_cf = 140 * GPa

# Glasfaser
f_gfs = 1250 * MPa
f_gfl = 500 * MPa
E_gf = 60 * GPa

# Diche
gamma = {"c": 2450, "s": 7850, "p": 7850, "a": 7850, "t": 450, "t24": 480,
         "u": 2300, "cf": 1550, "gf": 1700}  # kg/m3
# Kosten (CHF/m3) – nur der Vollständigkeit halber (S. 1)
c = {
    "c": 600, "s": 1.5 * 7850, "p": 6.0 * 7850, "a": 4.0 * 7850,
    "t": 2.0 * 450, "t24": 800, "u": 4000, "cf": 90 * 1550, "gf": 30 * 1700,
}

# =============================================================================
# 2) CO2-Werte e [kgCO2/m3] für die Plots (S. 10, inkl. 10%/90%-Fraktile)
# =============================================================================
e = {
    "c": 204, "c10": 189, "c90": 218,
    "s": 4466, "s10": 3134, "s90": 5662,
    "a": 5838, "a10": 2756, "a90": 9663,
    "p": 8590, "p10": 4004, "p90": 14630,
    "t": 130, "t10": 76, "t90": 188,
    "t24": 115, "t2410": 47, "t2490": 198,
    # ohne Fraktile (Werte S. 1)
    "u": 1100, "cf": 20 * 1550, "gf": 10 * 1700,
}


# Hinweis: e_p10, e_p90 und e_t2490 sind im Ausdruck abgeschnitten; sie wurden
# aus den auf S. 12 ausgegebenen Seitenlängen zurückgerechnet (4004 / 14630 / 198).


# =============================================================================
# 3) Querschnittsflächen
# =============================================================================
def A_single(c_e):
    """Einstoff-Querschnitt: A = 100 / (c_e * 1 m)."""
    return BUDGET / (c_e * L0)


def A_pc(sigma_cp, c_ec, c_ep):
    """Spannbeton: Spannstahlfläche A_p bei Vorspannung 0.7*f_p und Betonspannung sigma_cp."""
    return BUDGET / ((c_ep + 0.7 * 1.15 * f_pd / sigma_cp * c_ec) * L0)


def A_pc_concrete(sigma_cp, c_ec, c_ep):
    return 0.7 * 1.15 * f_pd / sigma_cp * A_pc(sigma_cp, c_ec, c_ep)


def A_rc(rho, c_ec, c_es):
    """Stahlbeton: Bruttofläche A_c mit A_s = rho * A_c."""
    return BUDGET / ((rho * c_es + (1 - rho) * c_ec) * L0)


# =============================================================================
# 4) Last-Verformungs-Beziehungen N(u) [N]
# =============================================================================
def _bilinear(eps, A, f_y, f_u, E, eps_u):
    """Elastisch - linear verfestigend bis eps_u, danach 0 (für |eps|)."""
    if eps <= f_y / E:
        return A * E * eps
    if eps <= eps_u:
        return A * (f_y + (eps - f_y / E) / (eps_u - f_y / E) * (f_u - f_y))
    return 0.0


@np.vectorize
def N_a(u, c_e):
    """Baustahl (Zug und Druck, symmetrisch)."""
    eps = abs(u / L0)
    return np.sign(u) * _bilinear(eps, A_single(c_e), f_ad, f_au, E_a, eps_au)


@np.vectorize
def N_s(u, c_e):
    """Betonstahl, nackt (Zug und Druck, symmetrisch)."""
    eps = abs(u / L0)
    return np.sign(u) * _bilinear(eps, A_single(c_e), f_sd, f_su, E_s, eps_su)


@np.vectorize
def N_p(u, c_e):
    """Spannstahl, nur Zug."""
    eps = u / L0
    if eps > 0:
        return _bilinear(eps, A_single(c_e), f_pd, f_pud, E_p, eps_pu)
    return 0.0


def _timber(u, c_e, E, f_t, f_c):
    eps = u / L0
    A = A_single(c_e)
    if eps > 0:
        return A * E * eps if E * eps <= f_t else 0.0
    return A * E * eps if E * abs(eps) <= f_c else 0.0


@np.vectorize
def N_t(u, c_e):
    """BSH GL24h (spröde in Zug und Druck)."""
    return _timber(u, c_e, E_t, f_ttd, f_tcd)


@np.vectorize
def N_t24(u, c_e):
    """Vollholz C24."""
    return _timber(u, c_e, E_t24, f_ttd24, f_tcd24)


@np.vectorize
def N_u(u, c_e):
    """UHPFRC: Zug verfestigend bis eps_uu, Druck linear bis f_ucd."""
    eps = u / L0
    A = A_single(c_e)
    if eps > 0:
        return _bilinear(eps, A, f_ued, f_utd, E_u, eps_uu)
    return A * E_u * eps if abs(eps) <= f_ucd / E_u else 0.0


@np.vectorize
def N_cf(u, c_e):
    """Kohlefaser (Langzeitfestigkeit)."""
    eps = u / L0
    return A_single(c_e) * E_cf * eps if E_cf * abs(eps) <= f_cfl else 0.0


@np.vectorize
def N_gf(u, c_e):
    """Glasfaser (Langzeitfestigkeit)."""
    eps = u / L0
    return A_single(c_e) * E_gf * eps if E_gf * abs(eps) <= f_gfl else 0.0


@np.vectorize
def N_pc(u, sigma_cp, c_ec, c_ep):
    """Spannbeton, Vorspannung auf 0.7 f_p, nur Zug, ohne Tension Stiffening."""
    eps = u / L0
    if eps <= 0:
        return 0.0
    eps_dec = sigma_cp / E_c
    d_eps = 0.7 * 1.15 * f_pd / E_p + sigma_cp / E_c * 0
    Ap = A_pc(sigma_cp, c_ec, c_ep)
    Ac = A_pc_concrete(sigma_cp, c_ec, c_ep)
    if eps <= eps_dec:
        return eps * (Ap * E_p + Ac * E_c)
    N_dec = eps_dec * (Ap * E_p + Ac * E_c)
    if eps <= f_pd / E_p - d_eps:
        return N_dec + Ap * E_p * (eps - eps_dec)
    if eps <= eps_pu - d_eps:
        return Ap * (f_pd + (eps - (f_pd / E_p - d_eps)) / (eps_pu - f_pd / E_p) * (f_pud - f_pd))
    return 0.0


@np.vectorize
def N_rc0(u, rho, c_ec, c_es):
    """Stahlbeton ohne Tension Stiffening, nur Zug (nicht geplottet)."""
    eps = u / L0
    if eps <= 0:
        return 0.0
    A = A_rc(rho, c_ec, c_es)
    if eps <= f_ctm / E_c:
        return eps * A * (E_c + rho * E_s)
    if eps <= f_sd / E_s:
        return max(rho * A * E_s * eps, f_ctm / E_c * A * (E_c + rho * E_s))
    if eps <= eps_su:
        return rho * A * (f_sd + (eps - f_sd / E_s) / (eps_su - f_sd / E_s) * (f_su - f_sd))
    return 0.0


# ---------- Stahlbeton mit Tension Stiffening ---------------------------------
def sigma_s(eps_s, f_s, f_t, E_sh):
    """Nackter Betonstahl, bilinear (f_t wird nicht verwendet, wie im Original)."""
    eps = abs(eps_s)
    if eps <= f_s / E_s:
        sig = eps * E_s
    else:
        sig = (eps - f_s / E_s) * E_sh + f_s
    if abs(eps_s) > eps_su:
        sig = sig * 1e-6
    return sig * np.sign(eps_s)


def sigma_cc(eps):
    """Beton auf Druck (Sargin-Parabel bis eps_c1d, dann konstant bis eps_c2d)."""
    eps_c = -eps
    k_sig = E_c / (400 * f_cd)
    zeta = eps_c / (-eps_c1d)
    if eps_c <= -eps_c1d:
        return -f_cd * (k_sig * zeta - zeta ** 2) / (1 + (k_sig - 2) * zeta)
    if eps_c <= -eps_c2d:
        return -f_cd
    return 0.0


def _eps_m_tcm(sig_r, s_r, D, f_s, E_sh, tb0, tb1):
    """Zuggurtmodell (Marti et al.): mittlere Stahldehnung bei Rissspannung sig_r,
    voll ausgebildetes Rissbild mit Rissabstand s_r."""
    if sig_r <= f_s:  # elastisch
        return (sig_r - tb0 * s_r / D) / E_s
    if sig_r - 2 * tb1 * s_r / D >= f_s:  # ganze Länge fliesst
        return f_s / E_s + (sig_r - f_s) / E_sh - tb1 * s_r / (D * E_sh)
    a = (sig_r - f_s) * D / (4 * tb1)  # teilweise plastisch
    b = s_r / 2 - a
    return (a * f_s / E_s + a * (sig_r - f_s) / (2 * E_sh)
            + b * (f_s - 2 * tb0 * b / D) / E_s) / (s_r / 2)


def sigma_sr(eps_sm, s_r, D, f_s, f_t, E_sh, rho, tb0, tb1):
    """TCM basic: Stahlspannung am Riss aus mittlerer Dehnung (Inversion von
    _eps_m_tcm). Bei Erreichen von f_t am Riss -> Bruch (0).
    Diese Funktion ist im Ausdruck ausgeblendet und wurde nach dem
    Zuggurtmodell rekonstruiert (stetiger Übergang zu sigma_srs ist geprüft)."""
    args = (s_r, D, f_s, E_sh, tb0, tb1)
    if eps_sm > _eps_m_tcm(f_t, *args):
        return 0.0
    lo, hi = 0.0, f_t
    for _ in range(80):  # Bisektion (monoton)
        mid = 0.5 * (lo + hi)
        if _eps_m_tcm(mid, *args) < eps_sm:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def sigma_srs(eps_sm, s_r, D, f_s, f_t, E_sh, rho, tb0, tb1):
    """TCM refined (vorgerissen, nach Seelhofer)."""
    n = E_s / E_c
    alpha = 1 + n * rho
    x1 = s_r / 2 * (np.sqrt(n ** 2 * rho ** 2 + E_s * eps_sm / tb0 * D / s_r) - n * rho)
    x1 = min(max(x1, 0.0), 0.5 * s_r)
    x20 = D * f_s * E_sh / (4 * tb1 * alpha * E_s)
    rad = 1 + 4 * alpha * E_s / E_sh * (
            s_r * tb1 / (D * f_s) * (alpha * E_s * eps_sm / f_s - n * rho) - tb1 / (4 * alpha * tb0))
    x2 = x20 * (np.sqrt(max(rad, 0.0)) - 1)
    x2 = min(max(x2, 0.0), 0.5 * s_r)
    if x1 * 4 * tb0 / D * (1 + n * rho) <= f_s:
        sig0 = x1 * 4 * tb0 / D * (1 + n * rho)
    else:
        sig0 = f_s + x2 * 4 * tb1 / D
    if x1 < 0.5 * s_r:
        return sig0
    return sigma_sr(eps_sm, s_r, D, f_s, f_t, E_sh, rho, tb0, tb1)


@np.vectorize
def N_rc(u, rho, c_ec, c_es):
    """Stahlbeton-Zuggurt mit Tension Stiffening (Zug) bzw. Beton + Stahl (Druck)."""
    eps = u / L0
    D = 20 * mm
    s_r = D / (4 * rho)
    E_sh = (f_su - f_sd) / (eps_su - f_sd / E_s)
    tb0 = 2 * f_ctm
    tb1 = 1 * f_ctm
    A = A_rc(rho, c_ec, c_es)
    if eps > 0:
        if eps <= eps_su:
            return rho * A * sigma_srs(eps, s_r, D, f_sd, f_su, E_sh, rho, tb0, tb1)
        return 0.0
    if eps >= eps_c2d:
        return A * sigma_cc(eps) + rho * A * sigma_s(eps, f_sd, f_su, E_sh)
    return 0.0


# ---------- Umschnürter Beton (confined concrete), nur Druck (S. 15/16) -------
# Grundlage Worksheet + SIA 262:2025
#   4.2.1.9  (29): k_c = 1 - 4*sigma_1/f_cd <= 4      -> f_c3 = k_c*f_cd <= 4*f_cd
#            (31): sigma_1 = -omega_c*f_cd*(Abminderung Bügelabstände)    (Rechteck)
#            Quadratische Bügel: omega_c = rho_w/2 * f_yd/f_cd (rho_w volumetrisch)
#            -> f_c3 = f_cd + 4*|sigma_1| = f_cd + 2*rho_w*f_yd*0.8  (= Worksheet,
#            Abminderung = 0.8 für s/d = 0.2)
#            Beton ausserhalb der Umschnürung (Überdeckung, kann abplatzen) darf nicht
#            angerechnet werden -> nur 95 % der Fläche (Annahme Worksheet).
#   4.2.1.10 Längsbewehrung gegen Ausknicken eng verbügeln.
#   5.5.4.2  Längsbewehrung Druckglieder: rho_l >= 0.6 % (sonst unbewehrt nach 5.5.1)
#   5.5.4.5  Längsbewehrung Druckglieder: rho_l <= 8 % (in der Regel)
#   5.5.4.7  Bügelabstand s <= 15*Ø_l,min, <= a_min, <= 300 mm; 5.5.4.9: Ø_Bügel >= Ø_l,max/3
ETA_CONF = 0.8          # Wirksamkeit der Umschnürung (s/d = 0.2)
CORE = 0.95             # umschnürter Flächenanteil (Überdeckung abgeplatzt)
KC_MAX = 4.0            # SIA 262, Gl. (29)
RHO_L_MIN = 0.006       # SIA 262, 5.5.4.2
RHO_L_MAX = 0.08        # SIA 262, 5.5.4.5

# Umschnürungsgrad, bei dem k_c = 4 erreicht wird (darüber keine Festigkeitszunahme mehr)
RHO_W_KCMAX = (KC_MAX - 1) * f_cd / (2 * f_sd * ETA_CONF)

# Gewählte Werte für Plot/Tabelle (Optimum: siehe study_rho_w())
RHO_W = RHO_W_KCMAX     # Umschnürungsbewehrung (volumetrisch) -> nur f_c3
RHO_L = RHO_L_MIN       # Längsbewehrung -> trägt mit min(E_s*eps, f_sd) mit


def A_cc(rho_w, rho_l, c_ec, c_es):
    """Bruttoquerschnitt umschnürter Beton: A = 100 / ((e_c + (rho_w + rho_l)*e_s) * 1 m)."""
    return BUDGET / ((c_ec + (rho_w + rho_l) * c_es) * L0)


def f_c3(f_c, rho_w):
    """Festigkeit umschnürter Beton: f_c3 = f_c + 2*rho_w*f_sd*0.8 <= 4*f_c (SIA 262 Gl. 29)."""
    return min(f_c + 2 * rho_w * f_sd * ETA_CONF, KC_MAX * f_c)


def eps_c3d(fc3, f_c=f_cd):
    """Bruchstauchung des umschnürten Betons."""
    return 0.002 * (5 * fc3 / f_c - 4)


def sigma_c3(fc3, eps_c, f_c=f_cd):
    """Spannung umschnürter Beton (Stauchung eps_c > 0 positiv, Spannung positiv)."""
    k_sig = E_c / (400 * f_c)
    zeta = eps_c / 0.002
    if eps_c <= 0.002:
        return fc3 * (k_sig * zeta - zeta**2) / (1 + (k_sig - 2) * zeta)
    if eps_c <= eps_c3d(fc3, f_c):
        return fc3
    return 0.0


def check_sia(rho_w, rho_l):
    """Hinweise zu den SIA-262-Grenzen."""
    msg = []
    if rho_l < RHO_L_MIN:
        msg.append(f"rho_l = {rho_l:.2%} < 0.6 % (SIA 262, 5.5.4.2): als unbewehrt zu bemessen")
    if rho_l > RHO_L_MAX:
        msg.append(f"rho_l = {rho_l:.2%} > 8 % (SIA 262, 5.5.4.5): besondere Massnahmen nötig")
    if rho_w > RHO_W_KCMAX + 1e-12:
        msg.append(f"rho_w = {rho_w:.2%} > {RHO_W_KCMAX:.2%}: k_c = 4 erreicht (SIA 262, Gl. 29), "
                   "zusätzliche Umschnürung bringt keine Festigkeit")
    return msg


@np.vectorize
def N_cc(u, rho_w, rho_l, c_ec, c_es):
    """Umschnürter Beton, nur Druck (N < 0).
    rho_w: Umschnürung (erhöht f_c3), rho_l: Längsbewehrung (A_s = rho_l*A).
    Mit Umschnürung (rho_w > 0) wird nur der Kern CORE*A angerechnet (SIA 262, 4.2.1.9)."""
    eps = -u / L0                                      # Stauchung positiv
    if eps <= 0:
        return 0.0
    fc3 = f_c3(f_cd, rho_w)
    if eps < min(eps_su, eps_c3d(fc3)):
        A = A_cc(rho_w, rho_l, c_ec, c_es)
        A_conc = CORE * A if rho_w > 0 else A
        return -(A_conc * sigma_c3(fc3, eps) + rho_l * A * min(E_s * eps, f_sd))
    return 0.0


def N_cc_max(rho_w, rho_l, c_ec=None, c_es=None):
    """Maximale Druckkraft |N| [N] des umschnürten Betons (Maximum über u)."""
    c_ec = e["c"] if c_ec is None else c_ec
    c_es = e["s"] if c_es is None else c_es
    eps_end = min(eps_su, eps_c3d(f_c3(f_cd, rho_w)))
    uu = -np.linspace(1e-6, eps_end * 0.999999, 2000) * L0
    return float(np.max(-N_cc(uu, rho_w, rho_l, c_ec, c_es)))


def study_rho_w(rho_w_max=0.15, rho_l_list=(RHO_L_MIN, 0.02, 0.04, RHO_L_MAX), n=301,
                fname="umschnuerung_variation.png"):
    """Variation des Umschnürungsgrads rho_w: N_max(rho_w) für mehrere rho_l
    innerhalb der SIA-Grenzen 0.6 % <= rho_l <= 8 %."""
    rws = np.unique(np.r_[np.linspace(0, rho_w_max, n), RHO_W_KCMAX])
    fig, ax = plt.subplots(figsize=(9.5, 5.8))
    res, best = {}, (0, None, None)
    print(f"\nUmschnürter Beton (Median e), k_c = 4 bei rho_w = {RHO_W_KCMAX:.2%}:")
    for rl in rho_l_list:
        Nm = np.array([N_cc_max(rw, rl) for rw in rws]) / 1e6
        res[rl] = Nm
        i = int(np.argmax(Nm))
        line, = ax.plot(rws * 100, Nm, lw=2, label=f"$\\rho_l$ = {rl:.1%}".replace(".0%", "%"))
        ax.plot(rws[i] * 100, Nm[i], "o", color=line.get_color(), ms=7)
        print(f"  rho_l = {rl:5.1%}:  N_max = {Nm[i]:6.2f} MN bei rho_w = {rws[i]:.2%}"
              f"   (rho_w = 0: {Nm[0]:.2f} MN)")
        if Nm[i] > best[0]:
            best = (Nm[i], rws[i], rl)
    ax.axvline(RHO_W_KCMAX * 100, color="k", ls=":", lw=1)
    ax.text(RHO_W_KCMAX * 100 + 0.2, ax.get_ylim()[0] + 0.3,
            f"$k_c$ = 4 (SIA 262, Gl. 29)\n$\\rho_w$ = {RHO_W_KCMAX:.2%}", fontsize=11, va="bottom")
    ax.set_xlabel("Umschnürungsgrad $\\rho_w$ (volumetrisch) [%]")
    ax.set_ylabel("max. Druckkraft $|N|$ [MN]")
    ax.set_title("Umschnürter Beton C30/37 – 100 kgCO$_2$ pro m Gurtlänge (Median $e$)")
    ax.grid(alpha=0.3)
    ax.legend(frameon=False, loc="upper right")
    fig.tight_layout()
    fig.savefig(fname, dpi=150)
    print(f"  -> Maximum: N = {best[0]:.2f} MN bei rho_w = {best[1]:.2%}, rho_l = {best[2]:.1%}")
    return rws, res, best


# =============================================================================
# 5) Plot (Layout nach Vorlage: Streubänder 10%/90%, Querschnitte massstäblich)
# =============================================================================
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D

RHO = 0.05
SIG_CP = 10 * MPa

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Liberation Serif", "STIXGeneral", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "font.size": 13,
})


def _fmt(x, nd=0):
    """Schweizer Tausendertrennzeichen: 12'345."""
    return f"{x:,.{nd}f}".replace(",", "'")


# Je Gurt: Median-Kurve + 10%/90%-Fraktile (-> Streuband).
# 'note': Beschriftung im Diagramm, 'xy': Zielpunkt u [mm] auf der Medianlinie,
# 'xytext': Textposition (u [mm], N [MN]), 'rad': Krümmung des Pfeils.
MATERIALS = [
    dict(key="a", name="Baustahl\nS355", color="#2f5597",
         f=lambda u, k: N_a(u, e[k]), keys=("a", "a10", "a90"),
         note_u=2.8, xytext=(3.35, 16.6), rad=-0.2),
    dict(key="s", name="Betonstahl\nB500B (nackt)", color="#7b4ea3",
         f=lambda u, k: N_s(u, e[k]), keys=("s", "s10", "s90"),
         note_u=-3.8, xytext=(-3.65, -19.6), rad=0.1),
    dict(key="rc", name="Stahlbeton\nC30/37, $\\rho_s$=5%", color="#2e9e44",
         f=lambda u, ks: N_rc(u, RHO, e[ks[0]], e[ks[1]]),
         keys=(("c", "s"), ("c10", "s10"), ("c90", "s90")),
         note_u=-2.6, xytext=(-2.15, -19.6), rad=0.2),
    dict(key="cc", name=f"Umschnürter Beton C30/37\n$\\rho_w$={RHO_W:.1%}, $\\rho_l$={RHO_L:.1%}", color="#0f6e6e",
         f=lambda u, ks: N_cc(u, RHO_W, RHO_L, e[ks[0]], e[ks[1]]),
         keys=(("c", "s"), ("c10", "s10"), ("c90", "s90")),
         note_u=-2.85, xytext=(-2.85, -23.4), rad=0.0),
    dict(key="pc", name="Stahlbeton C30/37,\nvorgespannt (10 MPa)", color="#d62728",
         f=lambda u, ks: N_pc(u, SIG_CP, e[ks[0]], e[ks[1]]),
         keys=(("c", "p"), ("c10", "p10"), ("c90", "p90")),
         note_u=3.35, xytext=(3.1, -4.0), rad=0.15),
    dict(key="t", name="Brettschichtholz\nGL24h", color="#e2541c",
         f=lambda u, k: N_t(u, e[k]), keys=("t", "t10", "t90"),
         note_u=0.9, xytext=(1.3, 16.2), rad=0.25),
    dict(key="t24", name="Vollholz\nC24", color="#d9b300",
         f=lambda u, k: N_t24(u, e[k]), keys=("t24", "t2410", "t2490"),
         note_u=0.6, xytext=(-0.6, 15.0), rad=-0.3),
]


def _hide_zero(u, N):
    """Nullwerte nach dem Versagen ausblenden (vertikaler Abfall auf 0 bleibt sichtbar)."""
    N = np.array(N, dtype=float)
    z = (N == 0) & (u != 0)
    keep = z & (np.roll(~z, 1) | np.roll(~z, -1))      # erster Nullpunkt neben Kurve
    N[z & ~keep] = np.nan
    return N


def _ultimate_u(f, k, sign=+1, u_max=0.3):
    """Grösste Verformung [m] (Zug: sign=+1, Druck: -1), bei der N != 0 ist."""
    uu = sign * np.linspace(1e-6, u_max, 30001)
    N = f(uu, k)
    nz = np.nonzero(np.abs(N) > 1.0)[0]
    return uu[nz[-1]] if len(nz) else 0.0


def _end_arrows(ax, items, x_edge, side, min_gap):
    """Pfeile + Bruchverformung am Diagrammrand für Kurven, die über den Rand hinaus gehen."""
    items = sorted(items, key=lambda t: t[0])
    y_txt = [y for y, *_ in items]
    for i in range(1, len(y_txt)):                    # Beschriftungen entzerren
        y_txt[i] = max(y_txt[i], y_txt[i - 1] + min_gap)
    shift = (np.mean([y for y, *_ in items]) - np.mean(y_txt))
    y_txt = [y + shift for y in y_txt]
    dx = 0.22 * side
    for (y, u_ult, col), yt in zip(items, y_txt):
        ax.annotate("", xy=(x_edge + dx, y), xytext=(x_edge, y),
                    arrowprops=dict(arrowstyle="-|>", color=col, lw=2.2, mutation_scale=16),
                    annotation_clip=False)
        ax.text(x_edge + dx + 0.05 * side, yt, f"{abs(u_ult) / mm:.0f} mm", color=col,
                ha="left" if side > 0 else "right", va="center", fontsize=14, clip_on=False)


def plot(u_min=-4, u_max=4, n=4001, ylim=(-27, 19), fname="last_verformung.png"):
    uu = np.linspace(u_min, u_max, n) * mm

    fig = plt.figure(figsize=(15, 13.5))
    gs = fig.add_gridspec(2, 1, height_ratios=[3.0, 1.0], hspace=0.12,
                          left=0.08, right=0.90, top=0.97, bottom=0.10)
    ax = fig.add_subplot(gs[0])
    axc = fig.add_subplot(gs[1])

    # --- Kurven und Streubänder ---------------------------------------------
    tens, comp = [], []
    for m in MATERIALS:
        f, (k50, k10, k90), col = m["f"], m["keys"], m["color"]
        N50, N10, N90 = (f(uu, k) / 1e6 for k in (k50, k10, k90))
        ax.fill_between(uu / mm, N10, N90, color=col, alpha=0.35, lw=0, zorder=1)
        for Nf in (N10, N90):
            ax.plot(uu / mm, _hide_zero(uu, Nf), color=col, ls=(0, (3, 2)), lw=1.1, zorder=2)
        ax.plot(uu / mm, _hide_zero(uu, N50), color=col, lw=2.8, zorder=4)
        m["N50"] = N50

        for sign, store, x_edge in ((+1, tens, u_max), (-1, comp, u_min)):
            u_ult = _ultimate_u(f, k50, sign)
            if abs(u_ult) > abs(x_edge) * mm:
                y_edge = f(x_edge * mm, k50) / 1e6
                store.append((float(y_edge), u_ult, col))

    _end_arrows(ax, tens, u_max, +1, min_gap=1.2)
    _end_arrows(ax, comp, u_min, -1, min_gap=1.2)

    # --- Beschriftungen mit Pfeilen ------------------------------------------
    for m in MATERIALS:
        u_t = m["note_u"]
        y_t = np.interp(u_t, uu / mm, m["N50"])
        ax.annotate(m["name"], xy=(u_t, y_t), xytext=m["xytext"], fontsize=15,
                    ha="center", va="center", color="k", zorder=6,
                    arrowprops=dict(arrowstyle="-|>", color="k", lw=1.1, mutation_scale=14,
                                    shrinkA=4, shrinkB=1,
                                    connectionstyle=f"arc3,rad={m['rad']}"))

    # --- Achsen im Ursprung mit Pfeilspitzen --------------------------------
    ax.set_xlim(u_min - 0.1, u_max + 0.3)
    ax.set_ylim(*ylim)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_position(("data", 0))
    ax.spines["bottom"].set_position(("data", 0))
    ax.spines["left"].set_zorder(5)
    ax.plot(1, 0, ">k", ms=11, transform=ax.get_yaxis_transform(), clip_on=False)
    ax.plot(0, 1, "^k", ms=11, transform=ax.get_xaxis_transform(), clip_on=False)
    ax.set_xticks(np.arange(u_min, u_max + 0.01, 0.5))
    ax.set_yticks(np.arange(-25, ylim[1], 2.5))
    ax.xaxis.set_major_formatter(lambda x, p: "" if abs(x) < 1e-9 else f"{x:.1f}")
    ax.yaxis.set_major_formatter(lambda y, p: "" if abs(y) < 1e-9 else f"{y:g}")
    ax.tick_params(direction="in", length=5, labelsize=13)
    for lab in ax.get_xticklabels() + ax.get_yticklabels():
        lab.set_bbox(dict(facecolor="white", edgecolor="none", alpha=0.7, pad=0.5))
    ax.text(0.15, ylim[1], "$N_{Rd}$ [MN]", fontsize=17, ha="left", va="top")
    ax.text(u_max + 0.35, -0.6, "$u$ [mm]", fontsize=17, ha="left", va="top", clip_on=False)

    box = dict(boxstyle="square,pad=0.3", fc="white", ec="k", lw=1.2)
    ax.text(2.6, 18.7, "Zuggurt", fontsize=18, ha="center", va="top", bbox=box)
    ax.text(-3.4, -26.6, "Druckgurt", fontsize=18, ha="center", va="bottom", bbox=box)

    # Legende Streuband
    handles = [Line2D([], [], color="k", lw=2.8, label="Median $e$"),
               Line2D([], [], color="k", lw=1.1, ls=(0, (3, 2)),
                      label="10%- / 90%-Fraktil $e$")]
    ax.legend(handles=handles, loc="upper left", frameon=False, fontsize=13)
    ax.text(-3.98, 13.2, "Budget: 100 kgCO$_2$ pro m Gurtlänge", fontsize=13, ha="left")

    # --- (c) Querschnitte massstäblich --------------------------------------
    _sections(axc)

    ax.text(-0.06, 1.0, "(a)", transform=ax.transAxes, fontsize=17, va="top")
    axc.text(-0.06, 1.0, "(b)", transform=axc.transAxes, fontsize=17, va="top")

    fig.savefig(fname, dpi=150, bbox_inches="tight", pad_inches=0.2)
    return fig


def _sections(axc):
    """Querschnitte (Median-e) als Quadrate im gleichen Massstab + A und g0k."""
    gk = {k: v * g / 1000 for k, v in gamma.items()}          # kN/m3
    A_rcm = A_rc(RHO, e["c"], e["s"])
    A_ccm = A_cc(RHO_W, RHO_L, e["c"], e["s"])
    A_p = A_pc(SIG_CP, e["c"], e["p"])
    A_cp = A_pc_concrete(SIG_CP, e["c"], e["p"])
    secs = [
        ("vorgespannter Beton|$\\sigma_{cp}$ = 10 MPa", "pc", A_cp + A_p,
         [f"$A_p$ = {_fmt(A_p * 1e6)} mm$^2$", f"$A_c$ = {_fmt(A_cp * 1e6)} mm$^2$"],
         A_cp * gk["c"] + A_p * gk["p"], A_p),
        ("Baustahl", "a", A_single(e["a"]),
         [f"$A$ = {_fmt(A_single(e['a']) * 1e6)} mm$^2$"], A_single(e["a"]) * gk["a"], None),
        ("Betonstahl", "s", A_single(e["s"]),
         [f"$A$ = {_fmt(A_single(e['s']) * 1e6)} mm$^2$"], A_single(e["s"]) * gk["s"], None),
        (f"Stahlbeton C30/37|$\\rho_s$ = {RHO:.0%}", "rc", A_rcm,
         [f"$A$ = {_fmt(A_rcm * 1e6)} mm$^2$"],
         A_rcm * ((1 - RHO) * gk["c"] + RHO * gk["s"]), None),
        (f"Umschnürter Beton|$\\rho_w$ = {RHO_W:.1%}, $\\rho_l$ = {RHO_L:.1%}", "cc", A_ccm,
         [f"$A$ = {_fmt(A_ccm * 1e6)} mm$^2$"],
         A_ccm * (gk["c"] + (RHO_W + RHO_L) * gk["s"]), None),
        ("Brettschichtholz|GL24h", "t", A_single(e["t"]),
         [f"$A$ = {_fmt(A_single(e['t']) * 1e6)} mm$^2$"], A_single(e["t"]) * gk["t"], None),
        ("Vollholz|C24", "t24", A_single(e["t24"]),
         [f"$A$ = {_fmt(A_single(e['t24']) * 1e6)} mm$^2$"], A_single(e["t24"]) * gk["t24"], None),
    ]
    col = {m["key"]: m["color"] for m in MATERIALS}
    W = 1150.0                                                 # Platz je Querschnitt [mm]
    for i, (name, key, A, lines, g0k, A_inner) in enumerate(secs):
        a = np.sqrt(A) / mm
        x0 = i * W
        if A_inner is None:
            axc.add_patch(Rectangle((x0, 0), a, a, color=col[key], alpha=0.7, lw=0))
        else:                                                  # Beton hell, Spannstahl voll
            axc.add_patch(Rectangle((x0, 0), a, a, color=col[key], alpha=0.25, lw=0))
            ai = np.sqrt(A_inner) / mm
            axc.add_patch(Rectangle((x0 + (a - ai) / 2, (a - ai) / 2), ai, ai,
                                    color=col[key], alpha=0.9, lw=0))
        title, _, sub = name.partition("|")
        txt = ["$\\bf{" + title.replace(" ", "~") + "}$"] + ([sub] if sub else [])
        txt += lines + [f"$a$ = {_fmt(a)} mm", f"$g_{{0k}}$ = {g0k:.1f} kN/m"]
        axc.annotate("\n".join(txt), xy=(x0, 0), xytext=(0, -10), textcoords="offset points",
                     ha="left", va="top", fontsize=12.5, linespacing=1.5, annotation_clip=False)
    axc.set_xlim(-30, len(secs) * W)
    axc.set_ylim(0, 1000)
    axc.set_aspect("equal", anchor="NW")
    axc.axis("off")


# =============================================================================
# 6) Querschnittsflächen und Seitenlängen (S. 12, quadratische Querschnitte)
# =============================================================================
def section_table():
    rows = []
    cases = [
        ("Baustahl", "a", lambda k: A_single(e[k]), ["a", "a10", "a90"]),
        ("Betonstahl", "s", lambda k: A_single(e[k]), ["s", "s10", "s90"]),
        ("Stahlbeton ρ=0.05", "rc", lambda ks: A_rc(RHO, e[ks[0]], e[ks[1]]),
         [("c", "s"), ("c10", "s10"), ("c90", "s90")]),
        ("Spannbeton σcp=10 MPa (A_p)", "pc", lambda ks: A_pc(SIG_CP, e[ks[0]], e[ks[1]]),
         [("c", "p"), ("c10", "p10"), ("c90", "p90")]),
        (f"Umschnürter Beton ρw={RHO_W:.3f}, ρl={RHO_L:.3f}", "cc", lambda ks: A_cc(RHO_W, RHO_L, e[ks[0]], e[ks[1]]),
         [("c", "s"), ("c10", "s10"), ("c90", "s90")]),
        ("BSH GL24h", "t", lambda k: A_single(e[k]), ["t", "t10", "t90"]),
        ("Vollholz C24", "t24", lambda k: A_single(e[k]), ["t24", "t2410", "t2490"]),
    ]
    for name, _, Af, keys in cases:
        row = [name]
        for k in keys:
            A = Af(k)
            row += [A * 1e6, np.sqrt(A) / mm]  # mm2, mm
        rows.append(row)

    header = ["Gurt", "A median [mm²]", "a median [mm]",
              "A 10% [mm²]", "a 10% [mm]", "A 90% [mm²]", "a 90% [mm]"]
    try:
        import pandas as pd
        df = pd.DataFrame(rows, columns=header).set_index("Gurt")
        return df
    except ImportError:
        return header, rows


if __name__ == "__main__":
    tab = section_table()
    try:
        import pandas as pd

        with pd.option_context("display.float_format", "{:,.1f}".format, "display.width", 200, "display.max_columns",
                               None):
            print(tab)
        tab.to_csv("querschnitte.csv", float_format="%.1f")
    except ImportError:
        print(tab)
    for w in check_sia(RHO_W, RHO_L):
        print("SIA-Hinweis:", w)
    plot()
    study_rho_w()
    plt.show()