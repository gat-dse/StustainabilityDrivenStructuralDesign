# VORSCHLAG: Querschnittsklasse fuer Brettsperrholzdecken (BSP, en: CLT, cross laminated timber)
# units: [m], [kg], [s], [N], [CHF]
#
# Niveau Vorbemessung, einachsig gespannter Plattenstreifen (analog wd_rec, section_type "wd_clt").
# Die Klasse liefert dieselben Attribute wie RectangularWood (mu_max, vu_p, g0k, ei1, phi, xi, ei_b, co2, ...),
# damit Member1D (Lasten, Durchbiegung, Eigenfrequenz, Schwingung nach HBT) ohne Aenderung verwendet werden kann.
#
# Berechnungsansatz (starre Verbundtheorie mit E90 = 0, nur Laengslagen tragen):
#   - Querschnittswerte I_ef, S_ef:            Mestek (2011), Gl. 1-3 / Gl. 6;  Schickhofer/Thiel, Gl. (1)
#   - Biegerandspannung, Rollschub (exakt):    Mestek (2011), Gl. 7, 9, 11, 12; EN 1995-1-1:2025, 8.1.11.2
#   - Schubsteifigkeit S_xz:                   Mestek (2011), Gl. 4
#   - Durchbiegung inkl. Schubverformung:      Mestek (2011), Gl. 14 -> als effektive Biegesteifigkeit ei1
#                                              (EN 1995-1-1:2025, 9.3.1.3(3): effektive Steifigkeit fuer CLT zulaessig)
#   - Festigkeiten/Steifigkeiten CL24:         EN 1995-1-1:2025, Anhang N.3, Tabelle N.1
#   - k_mod, k_def, gamma_M:                   EN 1995-1-1:2025, Tab. 5.2 (Ausschnitt), Tab. 5.5, Tab. 4.3
#   - Daempfung:                               EN 1995-1-1:2025, 9.3.1.1 (CLT: 0.025, mit schwimmendem Estrich 0.04)
#   - Brand (reduzierter Querschnitt):         Schickhofer/Thiel, Gl. (13), (14); EN 1995-1-2 (beta_0, d0, k_fi)
#
# Bewusste Vereinfachungen (Vorbemessung):
#   - Laengslagen alle gleiche Festigkeitsklasse (CL24), E90 = 0 (Querlagen tragen nicht in Spannrichtung).
#   - Starre Verbundtheorie fuer die Spannungen; gilt gut fuer l/h > ~20 (Mestek 3.1). Fuer gedrungene Platten
#     werden die Randspannungen leicht unterschaetzt -> Hinweis ueber self.l_h_ok.
#   - Schubverformung nur ueber die effektive Steifigkeit eines Einfeldtraegers unter Gleichlast beruecksichtigt
#     (Faktor auch fuer andere Systeme verwendet).
#   - Systembeiwert k_sys standardmaessig 1.0 (EN 1995-1-1:2025, 8.5.2 Anm. 2: deklarierte CLT-Festigkeiten koennen
#     die Systemwirkung bereits enthalten). Mestek / Schickhofer verwenden k_l = 1.1 -> als Parameter waehlbar.
#   - Keine Nachweise fuer Querdruck am Auflager, Einzellasten, Oeffnungen, Scheibenbeanspruchung.
#   - Tragsicherheit im Brandfall mit Restquerschnitt; Abfallen der Kohleschicht (Klebstoff nicht brandbestaendig)
#     vereinfacht ueber doppelte Abbrandrate in der jeweils naechsten Lage (siehe charring_depth).

import numpy as np
from struct_analysis import Section

# CL24 nach EN 1995-1-1:2025, Tabelle N.1 [Pa, kg/m3]
CL24 = dict(fm_k=24e6,      # Biegefestigkeit, Belastung senkrecht zur Ebene
            fv_k=3.5e6,     # Schubfestigkeit Laengslage, Belastung senkrecht zur Ebene
            fr_k=0.7e6,     # Rollschubfestigkeit
            E_mean=11.0e9,  # E-Modul parallel (Laengslagen)
            G_mean=650e6,   # Schubmodul Laengslagen
            Gr_mean=50e6,   # Rollschubmodul Querlagen
            rho_k=385)      # charakteristische Rohdichte

K_DEF_CLT = {1: 0.8, 2: 1.0}   # EN 1995-1-1:2025, Tabelle 5.5 (CLT, Nutzungsklasse 1 / 2; NKL 3 nicht zulaessig)

# Typische Standardaufbauten [Dicken der Lagen in m, von oben nach unten, Lage 0 = Decklage parallel zur Spannrichtung]
# 5-schichtige Aufbauten aus Mestek (2011), Abb. 6; uebrige: marktuebliche Aufbauten (herstellerneutral).
STANDARD_LAYUPS = {
    "CLT 60 3s":  [0.020, 0.020, 0.020],
    "CLT 80 3s":  [0.030, 0.020, 0.030],
    "CLT 90 3s":  [0.030, 0.030, 0.030],
    "CLT 100 3s": [0.040, 0.020, 0.040],
    "CLT 120 3s": [0.040, 0.040, 0.040],
    "CLT 100 5s": [0.020, 0.020, 0.020, 0.020, 0.020],
    "CLT 125 5s": [0.025, 0.025, 0.025, 0.025, 0.025],
    "CLT 140 5s": [0.040, 0.020, 0.020, 0.020, 0.040],
    "CLT 150 5s": [0.030, 0.030, 0.030, 0.030, 0.030],
    "CLT 160 5s": [0.040, 0.020, 0.040, 0.020, 0.040],
    "CLT 175 5s": [0.035, 0.035, 0.035, 0.035, 0.035],
    "CLT 180 5s": [0.040, 0.030, 0.040, 0.030, 0.040],
    "CLT 200 5s": [0.040, 0.040, 0.040, 0.040, 0.040],
    "CLT 220 7s": [0.040, 0.020, 0.040, 0.020, 0.040, 0.020, 0.040],
    "CLT 245 7s": [0.035, 0.035, 0.035, 0.035, 0.035, 0.035, 0.035],
    "CLT 260 7s": [0.040, 0.030, 0.040, 0.040, 0.040, 0.030, 0.040],
    "CLT 280 7s": [0.040, 0.040, 0.040, 0.040, 0.040, 0.040, 0.040],
}


class CrossLaminatedTimber(Section):
    # defines properties of a cross laminated timber slab strip (Brettsperrholzdecke), width b, uniaxial span
    def __init__(self, wood_type, layers, b=1.0, l0=None, orientations=None, nkl=1, k_mod=0.8, gamma_m=1.25,
                 k_sys=1.0, clt_prop=None, xi=0.025, ei_b=None, fire_mode=False):
        # wood_type:    Wood-Objekt aus struct_analysis (Produkt aus DB, z.B. PRO_ID 147 'CLT', MECH_PROP 'C24').
        #               Daraus: GWP, UBP, Graue Energie, Dichte, Raumlast. Festigkeiten/Steifigkeiten aus clt_prop.
        # layers:       Lagendicken [m] von oben nach unten, z.B. [0.04, 0.02, 0.04, 0.02, 0.04]
        # orientations: 0 = Laengslage (parallel Spannrichtung), 90 = Querlage; Standard: alternierend, beginnend mit 0
        # l0:           Spannweite [m] fuer die Beruecksichtigung der Schubverformung in ei1 (None: ohne Schubverformung)
        # nkl:          Nutzungsklasse (1 oder 2) -> k_def
        # k_mod:        0.8 (mittlere Lasteinwirkungsdauer, Nutzlast massgebend), EN 1995-1-1:2025 Tab. 5.2
        # gamma_m:      1.25 fuer CLT, EN 1995-1-1:2025 Tab. 4.3
        # k_sys:        Systembeiwert Biegung (1.0 konservativ, 1.1 nach Mestek Gl. 10 fuer n >= 4 Bretter)
        # clt_prop:     dict mit Abweichungen von CL24 (z.B. Werte aus ETA / DoP des Herstellers)
        # xi:           Daempfungsmass, EN 1995-1-1:2025, 9.3.1.1 (0.025 ohne, 0.04 mit schwimmendem Estrich)
        # ei_b:         Biegesteifigkeit quer zur Spannrichtung [Nm2/m]; None -> aus den Querlagen berechnet
        # fire_mode:    True -> Festigkeiten fuer den Brandfall (k_fi * f_k, gamma = k_mod = 1.0), intern verwendet
        section_type = "wd_clt"
        super().__init__(section_type)
        self.wood_type = wood_type
        self.prop = dict(CL24, **(clt_prop or {}))
        self.layers = [float(t) for t in layers]
        if orientations is None:
            orientations = [0 if i % 2 == 0 else 90 for i in range(len(self.layers))]
        self.orientations = list(orientations)
        self.n_layers = len(self.layers)
        self.b = b
        self.h = sum(self.layers)
        self.l0 = l0
        self.nkl, self.k_mod, self.gamma_m, self.k_sys = nkl, k_mod, gamma_m, k_sys
        self.fire_mode = fire_mode

        # --- Bemessungswerte der Festigkeiten -------------------------------------------------------------------
        # EN 1995-1-1:2025, 5.4.2(4): Abminderung der Biegefestigkeit fuer schmale Elemente t <= b <= 600 mm
        k_red_b = min(1.0, (self.b * 1e3) / 1200 + 0.5) if self.b < 0.6 else 1.0
        if fire_mode:  # Schickhofer/Thiel Gl. (14): f_d,fi = k_mod,fi * k_fi * f_k / gamma_M,fi, k_fi = 1.15
            k, g = 1.15, 1.0
        else:
            k, g = self.k_mod, self.gamma_m
        self.fm_d = k * self.k_sys * k_red_b * self.prop["fm_k"] / g
        self.fv_d = k * self.prop["fv_k"] / g
        self.fr_d = k * self.prop["fr_k"] / g

        # --- Querschnittswerte (E90 = 0) ------------------------------------------------------------------------
        self.E0 = self.prop["E_mean"]
        self.z_top = np.concatenate(([0.0], np.cumsum(self.layers)[:-1]))  # z = 0: Oberkante, z positiv nach unten
        self.z_mid = self.z_top + np.array(self.layers) / 2
        self.z_s, self.iy, self.a_ef = self.calc_effective_section(0)  # Laengslagen -> Haupttragrichtung
        self.s_max_long, self.s_max_cross = self.calc_static_moments()
        self.a_brutt = self.b * self.h

        # --- Tragwiderstand pro Streifenbreite b -----------------------------------------------------------------
        long_idx = [i for i, o in enumerate(self.orientations) if o == 0]
        z_edge = max(self.z_s - self.z_top[long_idx[0]],
                     self.z_top[long_idx[-1]] + self.layers[long_idx[-1]] - self.z_s)
        mu_el = self.fm_d * self.iy / z_edge                      # Mestek Gl. 7, 11 (Biegerandspannung)
        self.mu_max, self.mu_min = mu_el, -mu_el
        self.vu_long = self.fv_d * self.iy / self.s_max_long        # Schub in der Laengslage (Schwerachse)
        self.vu_roll = (self.fr_d * self.iy / self.s_max_cross      # Rollschub in der massgebenden Querlage
                        if self.s_max_cross > 0 else np.inf)        # Mestek Gl. 9, 12; EN 1995-1-1:2025 8.1.11.2
        vu_el = min(self.vu_long, self.vu_roll)
        self.vu_p, self.vu_n = vu_el, vu_el
        self.qs_class_n, self.qs_class_p = [3, 3]  # elastisch-elastisch (sproedes Versagen)

        # --- Steifigkeiten ----------------------------------------------------------------------------------------
        self.ei1_bend = self.E0 * self.iy                          # reine Biegesteifigkeit [Nm2]
        self.s_xz = self.calc_shear_stiffness()                    # Schubsteifigkeit [N]
        if l0:  # w = 5ql^4/(384 EI) + ql^2/(8 S) = 5ql^4/(384 EI_ef)  (Mestek Gl. 14)
            self.k_shear = 1 / (1 + 9.6 * self.ei1_bend / (self.s_xz * l0 ** 2))
            self.l_h_ok = l0 / self.h >= 20                        # starre Verbundtheorie ausreichend (Mestek 3.1)
        else:
            self.k_shear = 1.0
            self.l_h_ok = None
        self.ei1 = self.k_shear * self.ei1_bend                   # effektive Steifigkeit fuer Member1D [Nm2]
        self.phi = K_DEF_CLT[nkl]                                  # Kriechzahl = k_def (EN 1995-1-1:2025 Tab. 5.5)
        if ei_b is None:  # Querlagen tragen in Nebentragrichtung (pro m Breite), fuer Schwingungsnachweis HBT
            _, iy_b, _ = self.calc_effective_section(90)
            ei_b = self.E0 * iy_b / self.b
        self.ei_b = ei_b
        self.xi = xi

        # --- Eigenlast und Umweltwirkungen (Bruttoquerschnitt inkl. Querlagen) ------------------------------------
        self.g0k = self.a_brutt * wood_type.weight          # [N/m]
        self.g0k_b = self.g0k / self.b                       # [N/m2]
        self.co2 = self.a_brutt * wood_type.GWP * wood_type.density                       # [kg_CO2_eq/m]
        self.ubp = self.a_brutt * wood_type.UBP * wood_type.density                       # [UBP/m]
        self.graue_energie = self.a_brutt * wood_type.graue_energie * wood_type.density   # [kWh oil-eq/m]
        self.cost = self.a_brutt * wood_type.cost  # TODO: Kosten noch nicht implementiert (wie wd_rec)

    @classmethod
    def from_standard(cls, wood_type, name, **kwargs):
        # create section from a standard layup, e.g. CrossLaminatedTimber.from_standard(timber, "CLT 160 5s", l0=5.0)
        return cls(wood_type, STANDARD_LAYUPS[name], **kwargs)

    # ------------------------------------------------------------------------------------------------------------------
    def calc_effective_section(self, direction):
        # in: direction 0 (Haupttragrichtung, Laengslagen) or 90 (Nebentragrichtung, Querlagen)
        # out: centre of gravity z_s [m], effective moment of inertia I_ef [m4], effective area A_ef [m2]
        #      (Mestek Gl. 1, 2; only layers parallel to the direction are taken into account)
        idx = [i for i, o in enumerate(self.orientations) if o == direction]
        if not idx:
            return self.h / 2, 0.0, 0.0
        t = np.array([self.layers[i] for i in idx])
        z = np.array([self.z_mid[i] for i in idx])
        a_ef = self.b * t.sum()
        z_s = (t * z).sum() / t.sum()
        i_ef = self.b * (t ** 3 / 12 + t * (z - z_s) ** 2).sum()
        return z_s, i_ef, a_ef

    def static_moment(self, z):
        # first moment of the longitudinal layers above the level z with respect to z_s [m3] (Mestek Gl. 3)
        s = 0.0
        for t, zt, o in zip(self.layers, self.z_top, self.orientations):
            if o != 0 or zt >= z:
                continue
            t_part = min(t, z - zt)
            s += self.b * t_part * (self.z_s - (zt + t_part / 2))
        return abs(s)

    def calc_static_moments(self):
        # out: max. static moment in a longitudinal layer (at z_s) and in the critical cross layer [m3]
        #      In Querlagen ist der Schubfluss konstant (E90 = 0) -> S an der Lagenoberkante massgebend.
        s_long = self.static_moment(self.z_s)
        s_cross = max([self.static_moment(zt) for zt, o in zip(self.z_top, self.orientations) if o == 90],
                      default=0.0)
        return s_long, s_cross

    def calc_shear_stiffness(self):
        # equivalent shear stiffness S_xz [N] for width b (Mestek Gl. 4; a = distance of the outer layer centres)
        g = [self.prop["G_mean"] if o == 0 else self.prop["Gr_mean"] for o in self.orientations]
        if self.n_layers == 1:
            return 5 / 6 * g[0] * self.b * self.h
        a = self.z_mid[-1] - self.z_mid[0]
        compl = (self.layers[0] / (2 * g[0]) + sum(t / gi for t, gi in zip(self.layers[1:-1], g[1:-1]))
                 + self.layers[-1] / (2 * g[-1]))
        return self.b * a ** 2 / compl

    # ------------------------------------------------------------------------------------------------------------------
    # Nachweise am Bauteil (Member1D) – Ausnutzungsgrade fuer die Vorbemessung
    def utilization(self, member):
        # returns a dict of utilization ratios eta (<= 1.0 -> fulfilled); member: struct_analysis.Member1D
        eta = {}
        m_ed = max(abs(member.mEd_p), abs(member.mEd_n))
        eta["ULS bending"] = m_ed / self.mu_max
        eta["ULS shear long. layer"] = member.vEd / self.vu_long
        eta["ULS rolling shear"] = member.vEd / self.vu_roll
        eta["SLS w_install"] = member.w_install / member.w_install_adm
        eta["SLS w_use"] = member.w_use / member.w_use_adm
        eta["SLS w_app"] = member.w_app / member.w_app_adm
        eta["SLS f1"] = member.requirements.f1 / member.f1
        eta["SLS w_F (1kN)"] = member.wf_ed / (member.requirements.w_f_cdr1 * member.r1)
        eta["SLS v_e"] = member.ve_ed / member.ve_cd
        if member.f1 < member.requirements.f1:
            eta["SLS a_ed"] = member.a_ed / member.requirements.a_cd
        # vereinfachtes Kriterium Mestek 3.3: w(g + psi2*q) <= 6 mm (entspricht f1 ~ 7.2 Hz, nur Einfeldtraeger)
        eta["SLS w_perm <= 6mm"] = member.unit_def * member.q_per / 0.006
        t_fi = self.fire_resistance(member)
        eta["FIRE"] = member.requirements.t_fire / t_fi if t_fi > 0 else np.inf
        return eta

    # ------------------------------------------------------------------------------------------------------------------
    # Brand: Methode mit reduziertem Querschnitt (Schickhofer/Thiel 3.2.5, EN 1995-1-2)
    @staticmethod
    def charring_depth(layers, t, beta_0=0.65e-3, falloff=True):
        # charring depth d_char [m] after t [min] from one side; layers: thicknesses in burning order [m].
        # beta_0 = 0.65 mm/min (CLT / GL, EN 1995-1-2). falloff=True: Klebstoff nicht brandbestaendig ->
        # nach Durchbrand einer Lage faellt die Kohleschicht ab, die ersten 25 mm der naechsten Lage brennen
        # mit 2*beta_0 (vereinfachter Ansatz nach Frangi / EN 1995-1-2:2025).
        if not falloff:
            return beta_0 * t
        d, time, layer_end, idx = 0.0, 0.0, 0.0, 0
        layers = list(layers)
        fast_until = 0.0  # depth up to which the doubled rate applies
        dt = 0.25
        while time < t:
            if idx < len(layers) and d >= layer_end + layers[idx] - 1e-12:
                layer_end += layers[idx]
                idx += 1
                fast_until = d + 0.025
            beta = 2 * beta_0 if (idx > 0 and d < fast_until) else beta_0
            d += beta * min(dt, t - time)
            time += dt
        return d

    @staticmethod
    def remaining_section(section, fire, t=60, d0=0.007, beta_0=0.65e-3, falloff=True, t_min_layer=0.006):
        # residual CLT section after t [min]; fire = [bottom, left, top, right] (Member1D.fire)
        # d_ef = d_char + k0 * d0, k0 = min(t/20, 1)  (Schickhofer/Thiel Gl. 13)
        k0_d0 = min(t / 20, 1.0) * d0
        layers, ori = list(section.layers), list(section.orientations)
        for side in ([0] if fire[0] else []) + ([2] if fire[2] else []):
            if side == 2:  # fire from top: reverse to remove from the first layer
                layers, ori = layers[::-1], ori[::-1]
            rest = CrossLaminatedTimber.charring_depth(layers[::-1], t, beta_0, falloff) + k0_d0
            while rest > 0 and layers:  # remove from the bottom (end of list)
                if layers[-1] <= rest:
                    rest -= layers.pop()
                    ori.pop()
                else:
                    layers[-1] -= rest
                    rest = 0
            if layers and layers[-1] < t_min_layer:  # sehr duenne Restlagen vernachlaessigen (Schickhofer/Thiel)
                layers.pop()
                ori.pop()
            if side == 2:
                layers, ori = layers[::-1], ori[::-1]
        if 0 not in ori:
            return None  # keine tragende Laengslage mehr vorhanden
        return CrossLaminatedTimber(section.wood_type, layers, section.b, orientations=ori,
                                    k_sys=section.k_sys, clt_prop=section.prop, fire_mode=True)

    @staticmethod
    def fire_resistance(member, t_max=240, tol=0.5):
        # fire resistance [min]: largest t with q_d,fi <= q_u,fi (bisection, monotonic in t)
        s = member.section
        q_fi = member.gk + member.psi[2] * member.qk  # wie RectangularWood.fire_minimizer
        alpha_m = max(abs(a) for a in member.system.alpha_m)
        alpha_v = max(abs(a) for a in member.system.alpha_v)
        l = member.system.l_tot

        def ok(t):
            rs = CrossLaminatedTimber.remaining_section(s, member.fire, t)
            if rs is None:
                return False
            qu_fi = min(rs.mu_max / (alpha_m * l ** 2), rs.vu_p / (alpha_v * l))
            return qu_fi >= q_fi

        if not ok(0):
            return 0.0
        if ok(t_max):
            return float(t_max)
        lo, hi = 0.0, float(t_max)
        while hi - lo > tol:
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if ok(mid) else (lo, mid)
        return lo


# ----------------------------------------------------------------------------------------------------------------------
# Vorbemessung: duennster (bzw. GWP-minimaler) Standardaufbau, der alle Nachweise erfuellt
def opt_wd_clt(wood_type, system, floorstruc, requirements, qk, g2k=0.0, to_opt="h", layups=None, **section_kwargs):
    # returns (section, member, eta) of the best standard layup, or (None, None, None) if none fulfils all checks
    from struct_analysis import Member1D
    layups = layups or STANDARD_LAYUPS
    candidates = []
    for name, layers in layups.items():
        sec = CrossLaminatedTimber(wood_type, layers, l0=system.li_max, **section_kwargs)
        sec.name = name
        candidates.append(sec)
    key = (lambda s: s.h) if to_opt == "h" else (lambda s: s.co2)
    for sec in sorted(candidates, key=key):
        member = Member1D(sec, system, floorstruc, requirements, g2k=g2k, qk=qk)
        eta = sec.utilization(member)
        # SLS2 wie struct_optimization.failed_checks: a_ed nur, wenn f1 < f1_req; w_perm <= 6mm nur als Info
        relevant = {k: v for k, v in eta.items() if k not in ("SLS f1", "SLS w_perm <= 6mm")}
        if max(relevant.values()) <= 1.0:
            return sec, member, eta
    return None, None, None
