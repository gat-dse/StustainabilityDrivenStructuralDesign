from scipy.optimize import direct
import struct_analysis
from scipy.optimize import basinhopping, Bounds  # import Minimierungsfunktion aus dem SyiPy-Paket
from scipy.optimize import minimize  # import Minimierungsfunktion aus dem SyiPy-Paket
import numpy as np
import optuna
import math
import itertools


class RandomDisplacementBounds(object):
    # random displacement with bounds for basinhopping optimization
    def __init__(self, xmin, xmax, stepsize=0.1):
        self.xmin = xmin
        self.xmax = xmax
        self.stepsize = stepsize

    def __call__(self, x):
        """take a random step but ensure the new position is within the bounds """
        min_step = np.maximum(self.xmin - x, -self.stepsize)
        max_step = np.minimum(self.xmax - x, self.stepsize)

        random_step = np.random.uniform(low=min_step, high=max_step, size=x.shape)
        xnew = x + random_step

        return xnew



# define database
database_name = "database_261009.db"
# database_name = "dummy_sustainability.db"  # define database name
# create_dummy_database.create_database(database_name)  # create database


# create floor structure for solid reinforced concrete cross-section
bodenaufbau_rcdecke = [["'Parkett 2-Schicht werkversiegelt, 11 mm'", False, False],
                       ["'Unterlagsboden Zement, 85 mm'", False, False],
                       ["'Glaswolle'", 0.03, False]]
bodenaufbau_rc = struct_analysis.FloorStruc(bodenaufbau_rcdecke, database_name, name="massiv")

# create floor structure for ribbed reinforced concrete cross-section
bodenaufbau_rcdecke_slim = [["'Parkett 2-Schicht werkversiegelt, 11 mm'", False, False],
                       ["'Unterlagsboden Zement, 85 mm'", False, False],
                       ["'Glaswolle'", 0.03, False],["'Kies gebrochen'", 0.06, False]]
bodenaufbau_rc_rib = struct_analysis.FloorStruc(bodenaufbau_rcdecke_slim, database_name, name="Schuettung")




# ----------------------------------------------------------------------------------------------------------------------
# OPTIMIZATION OF RECTANGULAR CONCRETE CROSS-SECTIONS
# .......................................................................................................................
def opt_rc_rec(m, to_opt="GWP", criterion="ULS", max_iter=100, h_min=0.2, alg="TPE"):
    # Definition des stabilen, spanweitenabhängigen Startwerts L/25
    l0 = m.li_max
    h0 = l0 / 25

    # =========================================================================
    # FALL 1: DURCHLAUFTRÄGER (Zweistufige sequentielle Optimierung).
    # Zuerst wird QS im Feld optimiert (h, di_xu). bh und bdi_xi -> bounds
    # Dann wird mit fixem h die Bewehrung über der Stütze optimiert (di_xo)
    # Stababstände s_xu, s_xo sind fix (aus dem Ausgangsquerschnitt)
    # =========================================================================
    if min(m.system.alpha_m) < 0 and abs(min(m.system.alpha_m)) > max(m.system.alpha_m):

        # Optimierung mit TPE-Algorithmus
        # --- STUFE 1: Erst Geometrie (h) und Feldbewehrung (di_xu) im Feld optimieren ---
        optimise_stufe1 = "feld"

        # Statisch solider Schätzwert für die Stütze, gekoppelt an die Spannweite
        di_xo_schätzwert = max(0.012, min(0.032, 0.008 + (l0 - 4.0) * 0.002))
        di_xu0 = m.section.bw[0][0]

        if m.floorstruc.name == 'massiv':
            h_min_schall = 0.16
            bh = (max(0.08, m.section.hmin_c, h_min_schall), 0.8)

        elif m.floorstruc.name == 'Schuettung':
            h_min_schall = 0.13
            bh = (max(0.08, m.section.hmin_c, h_min_schall), 0.8)

        else:
            bh = (max(0.08, m.section.hmin_c), 0.8)

        bdi_xu = (max(0.008, m.section.di_xu_min), 0.04)
        bounds_stufe1 = [bh, bdi_xu]

        # Fixe Werte aus dem Querschnitt auslesen
        b = m.section.b
        s_xu, s_xo = m.section.bw[0][1], m.section.bw[1][1]  # Stababstände fix
        di_yu, s_yu = m.section.bw[2][0], m.section.bw[2][1]
        di_yo, s_yo = m.section.bw[3][0], m.section.bw[3][1]
        di_bw, s_bw, n_bw = m.section.bw_bg[0], m.section.bw_bg[1], m.section.bw_bg[2]
        phi, c_nom, xi, jnt_srch = m.section.phi, m.section.c_nom, m.section.xi, m.section.joint_surcharge
        co, st = m.section.concrete_type, m.section.rebar_type

        add_arg_stufe1 = [
            m.system, co, st, b,
            s_xu, di_xo_schätzwert, s_xo,
            di_yu, s_yu, di_yo, s_yo,
            m.floorstruc, m.requirements,
            to_opt, criterion,
            m.g2k, m.qk_area,
            optimise_stufe1
        ]

        # Zulässige Durchmesser filtern
        BEWEHRUNG_D = [
            0.008, 0.010, 0.012, 0.014,
            0.016, 0.018, 0.020, 0.022,
            0.026, 0.030, 0.034, 0.040
        ]

        di_xu_kandidaten = [
            d for d in BEWEHRUNG_D
            if bounds_stufe1[1][0] <= d <= bounds_stufe1[1][1]
        ]

        def objective_stufe1(trial):

            h = trial.suggest_float(
                "h",
                bounds_stufe1[0][0],
                bounds_stufe1[0][1],
                step=0.01
            )  # chooses float

            di_xu = trial.suggest_categorical(
                "di_xu",
                di_xu_kandidaten
            )  # chooses candidates from specified list

            try:
                return rc_rqs([h, di_xu], add_arg_stufe1, alg)
            except Exception:
                return 1e20

        study1 = optuna.create_study(
            direction="minimize",
            sampler=optuna.samplers.TPESampler(
                seed=42,
                multivariate=True
            )
        )

        # Startpunkt wie beim Basinhopping
        study1.enqueue_trial({
            "h": round(h0 / 0.01) * 0.01,
            "di_xu": min(di_xu_kandidaten, key=lambda d: abs(d - di_xu0)),
        })

        study1.optimize(
            objective_stufe1,
            n_trials=max_iter
        )

        h_opt = study1.best_params["h"]
        di_xu_opt = study1.best_params["di_xu"]

        # --- STUFE 2: Höhe h_opt und di_xu_opt fixieren -> Stützenbewehrung (di_xo) ermitteln ---
        optimise_stufe2 = "stuetze_fix_h"

        bounds_stufe2 = [
            (max(0.008, m.section.di_xo_min), 0.04)
        ]

        add_arg_stufe2 = [
            m.system, co, st, b,
            s_xu, s_xo,
            di_yu, s_yu,
            di_yo, s_yo,
            m.floorstruc,
            m.requirements,
            to_opt, criterion,
            m.g2k, m.qk_area,
            h_opt, di_xu_opt,
            optimise_stufe2
        ]

        di_xo_kandidaten = [
            d for d in BEWEHRUNG_D
            if bounds_stufe2[0][0] <= d <= bounds_stufe2[0][1]
        ]

        def objective_stufe2(trial):

            di_xo = trial.suggest_categorical(
                "di_xo",
                di_xo_kandidaten
            )

            try:
                return rc_rqs([di_xo], add_arg_stufe2, alg)
            except Exception:
                return 1e20

        study2 = optuna.create_study(
            direction="minimize",
            sampler=optuna.samplers.TPESampler(
                seed=42,
                multivariate=True
            )
        )

        # Startwerte
        study2.enqueue_trial({
            "di_xo": min(
                di_xo_kandidaten,
                key=lambda d: abs(d - di_xo_schätzwert)
            ),
        })

        study2.optimize(
            objective_stufe2,
            n_trials=max_iter
        )

        # Resultate zusammenführen (s_xu, s_xo bleiben fix)
        h = h_opt
        di_xu = di_xu_opt
        di_xo = study2.best_params["di_xo"]

    # =========================================================================
    # FALL 2: SIMPLE BEAM / EINFELDTRÄGER
    # =========================================================================
    else:
        # Optimierung mit TPE-Algorithmus (Optuna)
        optimise = "unten"
        di_xu0 = m.section.bw[0][0]

        if m.floorstruc.name == 'massiv':
            h_min_schall = 0.16
            bh = (max(0.08, m.section.hmin_c, h_min_schall), 0.8)

        elif m.floorstruc.name == 'Schuettung':
            h_min_schall = 0.13
            bh = (max(0.08, m.section.hmin_c, h_min_schall), 0.8)

        else:
            bh = (max(0.08, m.section.hmin_c), 0.8)

        bdi_xu = (max(0.008, m.section.di_xu_min), 0.04)

        bounds = [bh, bdi_xu]

        # Fixe Werte aus dem Querschnitt auslesen
        b = m.section.b
        s_xu, di_xo, s_xo = m.section.bw[0][1], m.section.bw[1][0], m.section.bw[1][1]  # Stababstände fix
        di_yu, s_yu = m.section.bw[2][0], m.section.bw[2][1]
        di_yo, s_yo = m.section.bw[3][0], m.section.bw[3][1]
        di_bw, s_bw, n_bw = m.section.bw_bg[0], m.section.bw_bg[1], m.section.bw_bg[2]
        phi, c_nom, xi, jnt_srch = m.section.phi, m.section.c_nom, m.section.xi, m.section.joint_surcharge
        co, st = m.section.concrete_type, m.section.rebar_type

        add_arg = [
            m.system, co, st, b,
            s_xu, di_xo, s_xo,
            di_yu, s_yu,
            di_yo, s_yo,
            m.floorstruc, m.requirements,
            to_opt, criterion,
            m.g2k, m.qk_area,
            optimise
        ]

        BEWEHRUNG_D = [
            0.008, 0.010, 0.012, 0.014,
            0.016, 0.018, 0.020, 0.022,
            0.026, 0.030, 0.034, 0.040
        ]

        di_xu_kandidaten = [
            d for d in BEWEHRUNG_D
            if bounds[1][0] <= d <= bounds[1][1]
        ]

        def objective(trial):

            h = trial.suggest_float(
                "h",
                bounds[0][0],
                bounds[0][1],
                step=0.01
            )

            di_xu = trial.suggest_categorical(
                "di_xu",
                di_xu_kandidaten
            )

            try:
                return rc_rqs([h, di_xu], add_arg, alg)
            except Exception:
                return 1e20

        study = optuna.create_study(
            direction="minimize",
            sampler=optuna.samplers.TPESampler(seed=42)
        )

        study.enqueue_trial({
            "h": round(h0 / 0.01) * 0.01,
            "di_xu": min(di_xu_kandidaten, key=lambda d: abs(d - di_xu0)),
        })

        study.optimize(
            objective,
            n_trials=max_iter
        )

        h = study.best_params["h"]
        di_xu = study.best_params["di_xu"]

    # Generierung des optimierten End-Querschnitts
    optimized_section = struct_analysis.RectangularConcrete(co, st, b, h, di_xu, s_xu, di_xo, s_xo, di_yu, s_yu, di_yo,
                                                            s_yo, di_bw, s_bw, n_bw, phi, c_nom, xi, jnt_srch)
    return optimized_section


# inner function for optimizing reinforced concrete section
def rc_rqs(var, add_arg, alg="basinhoppin"):

    optimise = add_arg[-1]

    if optimise == "feld":

        # Stufe 1 (Durchlaufträger): h, di_xu variabel; s_xu, s_xo fix
        h, di_xu = var

        system = add_arg[0]
        concrete = add_arg[1]
        reinfsteel = add_arg[2]
        b = add_arg[3]

        s_xu = add_arg[4]
        di_xo = add_arg[5]
        s_xo = add_arg[6]

        di_yu, s_yu = add_arg[7:9]
        di_yo, s_yo = add_arg[9:11]

        floorstruc = add_arg[11]
        criteria = add_arg[12]
        to_opt = add_arg[13]
        criterion = add_arg[14]
        g2k = add_arg[15]
        qk = add_arg[16]

    elif optimise == "stuetze_fix_h":

        # Stufe 2 (Durchlaufträger): nur di_xo variabel; h, di_xu, s_xu, s_xo fix
        di_xo = var[0]

        system = add_arg[0]
        concrete = add_arg[1]
        reinfsteel = add_arg[2]
        b = add_arg[3]

        s_xu = add_arg[4]
        s_xo = add_arg[5]

        di_yu, s_yu = add_arg[6:8]
        di_yo, s_yo = add_arg[8:10]

        floorstruc = add_arg[10]
        criteria = add_arg[11]
        to_opt = add_arg[12]
        criterion = add_arg[13]
        g2k = add_arg[14]
        qk = add_arg[15]

        h = add_arg[-3]
        di_xu = add_arg[-2]

    elif optimise == "unten":

        # Einfeldträger: h, di_xu variabel; s_xu, di_xo, s_xo fix
        h, di_xu = var

        system = add_arg[0]
        concrete = add_arg[1]
        reinfsteel = add_arg[2]
        b = add_arg[3]

        s_xu = add_arg[4]
        di_xo = add_arg[5]
        s_xo = add_arg[6]

        di_yu, s_yu = add_arg[7:9]
        di_yo, s_yo = add_arg[9:11]

        floorstruc = add_arg[11]
        criteria = add_arg[12]
        to_opt = add_arg[13]
        criterion = add_arg[14]
        g2k = add_arg[15]
        qk = add_arg[16]



    # Querschnitt erzeugen
    section = struct_analysis.RectangularConcrete(concrete, reinfsteel, b, h, di_xu, s_xu, di_xo, s_xo, di_yu, s_yu,
                                                  di_yo, s_yo)

    # create member
    member = struct_analysis.Member1D(section, system, floorstruc, criteria, g2k, qk)
    member.calc_qk_zul_gzt()  # calculate admissible live load

    # define penalty1, if ULS is not fulfilled
    penalty1 = 1e3 * max(member.qk - member.qk_zul_gzt, 0)

    # define penalty2, if SLS1 (deflections) are not fulfilled
    # 1. Fall: Reine Kragarme oder Bauteile mit reinem negativen Moment ("oben")
    if optimise == "oben":
        if abs(member.mkd_n) < abs(member.section.mr_n): #falls Biegemoment kleiner ist als Rissmoment ist QS ungerissen
            d1, d2, d3 = [member.w_install - member.w_install_adm, member.w_use - member.w_use_adm,
                          member.w_app - member.w_app_adm] #Durchbiegung ungerissen
        else:
            d1, d2, d3 = [member.w_install_ger - member.w_install_adm, member.w_use_ger - member.w_use_adm,
                          member.w_app_ger - member.w_app_adm] #Durchbiegung gerissen?

    # 2. Fall: Reiner Einfeldträger ("unten") -> Prüft nur das Feld
    elif optimise == "unten":
        if member.mkd_p < member.section.mr_p: #falls positives Biegemoment kleiner ist als Rissmoment, ist QS ungerissen
            d1, d2, d3 = [member.w_install - member.w_install_adm, member.w_use - member.w_use_adm,
                          member.w_app - member.w_app_adm] #Durchbiegung ungerissen
        else:
            d1, d2, d3 = [member.w_install_ger - member.w_install_adm, member.w_use_ger - member.w_use_adm,
                          member.w_app_ger - member.w_app_adm]

    # 3. Fall: Der Durchlaufträger (wird hier über "feld" und "stuetze_fix_h" abgefangen)
    else:
        # UNGERISSEN NUR WENN: Feld ungerissen UND Stütze ungerissen
        # Hinweis: Da mr_n negativ definiert ist, prüfen wir mit absoluten Werten.
        if member.mkd_p < member.section.mr_p and abs(member.mkd_n) < abs(member.section.mr_n):
            # Für beide Bereiche ist Biegemoment < Rissmoment und somit Zustand I -> Ungerissen
            d1, d2, d3 = [member.w_install - member.w_install_adm,
                          member.w_use - member.w_use_adm,
                          member.w_app - member.w_app_adm]
        else:
            # Sobald für Feld ODER Stütze das Biegemoment > Rissmoment wird, gilt Zustand II -> Gerissen rechnen
            d1, d2, d3 = [member.w_install_ger - member.w_install_adm,
                          member.w_use_ger - member.w_use_adm,
                          member.w_app_ger - member.w_app_adm]

    penalty2 = 1e5 * max(d1, d2, d3, 0)



    # define penalty3, if SLS2 (vibrations) are not fulfilled
    pen_a = 0
    pen_w = 0
    pen_v = 0

    if isinstance(member.f1, complex):
        print("Komplexe f1!")
        print("h =", h)
        print("di_xu =", di_xu)
        print("di_xo =", di_xo)

    if member.f1 < member.requirements.f1:
        penalty3 = max(pen_a * 1e2, pen_w * 1e5, pen_v * 1e3, 0)
    else:
        penalty3 = max(pen_w * 1e5, pen_v * 1e3, 0)

    # define penalty4, if fire resistance is not fulfilled
    member.get_fire_resistance()
    penalty4 = max(member.requirements.t_fire - member.fire_resistance, 0)

    # optimize ULS only
    if criterion == "ULS":
        if to_opt == "GWP":
            return member.section.co2 * (1 + penalty1)
        elif to_opt == "h":
            return member.section.h * (1 + penalty1)

    # optimize SLS1 (deflections). Make sure, that also ULS is fulfilled
    elif criterion == "SLS1":
        if to_opt == "GWP":
            return member.section.co2 * (1 + penalty2)
        elif to_opt == "h":
            return member.section.h * (1 + penalty2)

    # optimize SLS2 (vibrations). Make sure, that also ULS is fulfilled
    elif criterion == "SLS2":
        if to_opt == "GWP":
            to_minimize = member.section.co2 * (1 + penalty3)
            return to_minimize
        elif to_opt == "h":
            to_minimize = member.section.h * (1 + penalty3)
            return to_minimize

    # optimize fire resistance only
    elif criterion == "FIRE":
        if to_opt == "GWP":
            return member.section.co2 * (1 + penalty4)
        elif to_opt == "h":
            return member.section.h * (1 + penalty4)

    # optimize solution, which fulfills all requirements (ULS, SLS1 and SLS2, FIRE)
    elif criterion == "ENV":
        if to_opt == "GWP":
            to_minimize = member.section.co2 * (1 + penalty1 + penalty2 + penalty3 + penalty4)
        elif to_opt == "h":
            to_minimize = member.section.h * (1 + penalty1 + penalty2 + penalty3 + penalty4)
    else:
        to_minimize = 99
        print("criterion " + criterion + " is not defined")
        print("criterion has to be 'ULS', 'SLS1', 'SLS2', 'FIRE' or 'ENV'")

    return to_minimize






#OPTIMIZATION OF RIB CONCRETE CROSS-SECTIONS
#.......................................................................................................................
def opt_rc_rib(m, to_opt="GWP", criterion="ULS", max_iter=100, alg="basinhoppin"):
    # definition of initial values for variables, which are going to be optimized
    h_w0 = m.section.h - m.section.h_f  # start value for height corresponds to 1/20 of system length
    h_f0 = m.section.h_f
    di_x_w0 = m.section.bw_r[0]  # start value for rebar diameter 40 mm
    di_pb_bw0 = m.section.bw_bg_r[0]  # start value for rebar diameter 8 mm
    b_w0 = m.section.b_w
    b0 = m.section.b

    # Fallunterscheidung für Bodenaufbau, falls die Flanchstärke über 16 cm ist (Mindestanforderung Schallschutz)
    # kann der Bodenaufbau reduziert werden auf den Aufbau ohne Schüttung
    # if m.section.h_f >= 0.16:
    #    floorstruc = bodenaufbau_rc
    #    m.floorstruc = bodenaufbau_rc
    # else:
    #    floorstruc = bodenaufbau_rc_rib
    #    m.floorstruc = bodenaufbau_rc_rib

    # Definition von maximaler effektiver Breite beff für Einfeldträger (Optimierung Durchlaufträger aktuell in anderem File)
    l0 = m.li_max
    b_eff_max = 2 * 0.2 * l0 + b_w0  # max.eff. Breite mit l0 =l für Einfeldträger: 2*beff,i + bw und beff,i,max = 0.2*l0

    var0 = [h_w0, h_f0, di_x_w0, b_w0, b0, di_pb_bw0]

    # define bounds of variables
    if m.floorstruc.name == 'massiv':
        h_min_schall = 0.16
        h_fix = max(0.08, m.section.hmin_c, h_min_schall)
        bh_f = (h_fix, h_fix)
        # bh_f = (max(0.08, m.section.hmin_c, h_min_schall), 0.5)  # h_f_max_dynamisch)

    elif m.floorstruc.name == 'Schuettung':
        h_min_schall = 0.13
        h_fix = max(0.08, m.section.hmin_c, h_min_schall)
        bh_f = (h_fix, h_fix)
        # bh_f = (max(0.08, m.section.hmin_c, h_min_schall), 0.5)  # h_f_max_dynamisch)

    else:
        h_fix = max(0.08, m.section.hmin_c)
        bh_f = (h_fix, h_fix)
        # bh_f = (max(0.08, m.section.hmin_c), 0.5)  # h_f_max_dynamisch)

    # bh_f = (max(0.08, m.section.hmin_c), 0.5)  # height between max(8 cm, Mindestplattenstärke für 4 Bewehrungslsagen) and 50 cm
    bh_w = (0.04, 1.2)  # height between 10 cm and 2.0 m
    bdi_x_w = (0.008, 0.04)  # diameter of rebars between 8 mm and 40 mm
    bdi_pb_bw = (0.008, 0.016)  # diameter of rebars between 8mm and 16 mm for stirrups
    # Statische Grenze für Rippenbreite. Das exakte bewehrungsabhängige Minimum wird dynamisch über eine Penalty in der Zielfunktion erzwungen.
    bb_w = (0.15, 0.4)  # 15 cm entspricht Mindeststegbreite für R60

    # Dynamische Grenze für Rippenbreite
    # b_w_min_c = (2 * m.section.c_nom +  # 2 * Überdeckung
    #                  0.032 * (m.section.bw_r[1] - 1)  # (n-1) * Grösstkorn zwischen Bew.-Stäben in Längsrichtung
    #                  + 2 * m.section.bw_bg_r[0]  # 2 * Bügeldurchmesser
    #                  + m.section.bw_r[0] * m.section.bw_r[1]  # n * Durchmesser
    #                  +0.03 )
    # bb_w = (max(0.15, b_w_min_c), 0.4)  # rib width between 15 and 40 cm # 15 cm entspricht Mindeststegbreite für R60

    bb = (0.4, 3.8)  # rib spacing between 0.4 and 2.5 m
    #bb = (1.0,
    #     1.0)  # rib spacing between 0.4 und 3.8 m (max Rippenbreite für Einfeldträger, sodass GZT für Platte in Querrichtung i.O.)

    bounds = [bh_w, bh_f, bdi_x_w, bb_w, bb, bdi_pb_bw]

    s_xu, s_xo = m.section.bw[0][1], m.section.bw[1][1]
    di_xu, di_xo = max(0.008, m.section.di_xu_min, m.section.bw[0][0]), max(0.008, m.section.di_xo_min,
                                                                            m.section.bw[1][0])  #

    s_pb_bw, n_pb_bw = m.section.bw_bg_r[1], m.section.bw_bg_r[2]
    n_x_w = m.section.bw_r[1]
    n_lagen = 1
    phi, c_nom, xi, jnt_srch = m.section.phi, m.section.c_nom, m.section.xi, m.section.joint_surcharge

    co, st = m.section.concrete_type, m.section.rebar_type
    add_arg = [m.system, co, st, l0, di_xu, s_xu, di_xo, s_xo, n_x_w, s_pb_bw, n_pb_bw, m.floorstruc,
               m.requirements, to_opt, criterion, m.g2k, m.qk_area, c_nom, phi, xi, jnt_srch]


    # TPE-Algorithmus mit Optuna

    BEWEHRUNG_D = [
        0.008, 0.010, 0.012, 0.014,
        0.016, 0.018, 0.020, 0.022,
        0.026, 0.030, 0.034, 0.040
    ]

    BUEGEL_D = [
        0.008, 0.010, 0.012, 0.014, 0.016
    ]

    N_X_W = [1, 2, 3, 4, 5, 6, 7, 8]

    N_LAGEN = [1, 2]
    # ggf. vergrössern falls konstruktiv zulässig

    di_x_w_kandidaten = [
        d for d in BEWEHRUNG_D
        if bdi_x_w[0] <= d <= bdi_x_w[1]
    ]

    di_pb_bw_kandidaten = [
        d for d in BUEGEL_D
        if bdi_pb_bw[0] <= d <= bdi_pb_bw[1]
    ]


    def objective_rib(trial):

        h_w = trial.suggest_float(
            "h_w",
            bh_w[0],
            bh_w[1],
            step=0.01
        )

        h_f = trial.suggest_float(
            "h_f",
            bh_f[0],
            bh_f[1],
            step=0.01
        )

        b_w = trial.suggest_float(
            "b_w",
            bb_w[0],
            bb_w[1],
            step=0.01
        )

        b = trial.suggest_float(
            "b",
            bb[0],
            bb[1],
            step=0.01
        )

        di_x_w = trial.suggest_categorical(
            "di_x_w",
            di_x_w_kandidaten
        )

        di_pb_bw = trial.suggest_categorical(
            "di_pb_bw",
            di_pb_bw_kandidaten
        )

        n_x_w = trial.suggest_categorical(
            "n_x_w",
            N_X_W
        )

        n_lagen = trial.suggest_categorical(
            "n_lagen",
            N_LAGEN
        )

        try:

            return rc_rib_rqs(
                [
                    h_w,
                    h_f,
                    di_x_w,
                    b_w,
                    b,
                    di_pb_bw,
                    n_x_w,
                    n_lagen
                ],
                add_arg,
                alg="TPE"
            )

        except Exception:
            return 1e20

    study = optuna.create_study(
        direction="minimize",
        sampler=optuna.samplers.TPESampler(seed=42)
    )

    study.enqueue_trial({

        "h_w": round(h_w0 / 0.01) * 0.01,
        "h_f": round(h_f0 / 0.01) * 0.01,

        "di_x_w": min(
            di_x_w_kandidaten,
            key=lambda d: abs(d - di_x_w0)
        ),

        "b_w": round(b_w0 / 0.01) * 0.01,
        "b": round(b0 / 0.01) * 0.01,

        "di_pb_bw": min(
            di_pb_bw_kandidaten,
            key=lambda d: abs(d - di_pb_bw0)
        ),

        "n_x_w": n_x_w,

        "n_lagen": n_lagen
    })

    study.optimize(
        objective_rib,
        n_trials=max_iter
    )

    h_w = study.best_params["h_w"]
    h_f = study.best_params["h_f"]
    di_x_w = study.best_params["di_x_w"]
    b_w = study.best_params["b_w"]
    b = study.best_params["b"]
    di_pb_bw = study.best_params["di_pb_bw"]
    n_x_w = study.best_params["n_x_w"]
    n_lagen = study.best_params["n_lagen"]

    optimized_section = struct_analysis.RibbedConcrete(co, st, l0, b, b_w, h_f + h_w, h_f, di_xu, s_xu, di_xo, s_xo,
                                                       di_x_w, n_x_w, di_pb_bw, s_pb_bw, n_pb_bw, n_lagen, phi, c_nom, xi,
                                                       jnt_srch)
    # print(l0,round(b,5),round(b_w,5), round(h_w,5), round(h_f,5), di_x_w)

    return optimized_section


# inner function for optimizing reinforced concrete section
def rib_b_w_required(c_nom, di_x_w, n_x_w, di_pb_bw, n_lagen):
    # required rib width for the current longitudinal bars (di_x_w, n_x_w) and stirrups (di_pb_bw)
    b_w_min_c = (2 * c_nom +  # 2 * Überdeckung
                         0.032 * (n_x_w - 1) +  # (n-1) * Grösstkorn zwischen Längsstäben
                         2 * di_pb_bw +  # 2 * AKTUELLER Bügeldurchmesser
                         di_x_w * n_x_w  # n * AKTUELLER Längsstabdurchmesser
                         + 0.01)  # Reserve 10 mm
    b_w_min_c2 = (2 * c_nom +  # 2 * Überdeckung
                  0.032 * (math.ceil(
                n_x_w / 2) - 1)  # (n/2-1) * Grösstkorn zwischen Bew.-Stäben in Längsrichtung
                  + 2 * di_pb_bw  # 2 * Bügeldurchmesser
                  + di_x_w * math.ceil(n_x_w / 2)  # n/2 * Durchmesser
                  )
    return max(0.15, b_w_min_c2 if n_lagen == 2 and n_x_w > 1 else b_w_min_c)


def rc_rib_rqs(var, add_arg, alg="basinhoppin"):


    h_w, h_f, di_x_w, b_w, b, di_pb_bw, n_x_w, n_lagen = var

    system = add_arg[0]
    concrete = add_arg[1]
    reinfsteel = add_arg[2]
    l0 = add_arg[3]

    di_xu = add_arg[4]
    s_xu = add_arg[5]
    di_xo = add_arg[6]
    s_xo = add_arg[7]

    s_pb_bw = add_arg[9]
    n_pb_bw = add_arg[10]

    floorstruc = add_arg[11]
    criteria = add_arg[12]
    to_opt = add_arg[13]
    criterion = add_arg[14]
    g2k = add_arg[15]
    qk = add_arg[16]
    c_nom = add_arg[17]
    phi = add_arg[18]
    xi = add_arg[19]
    jnt_srch = add_arg[20]


    #TODO: nicht alle Inputs für Ribbed Concrete sind hier übertragen


    #TODO Penalty für bw hier integrieren

    if n_lagen == 2 and n_x_w == 1:
        n_lagen = 1

    #TODO Flanschbreiten check mit 2 Lagen hier einfügen

    b_w_erforderlich = rib_b_w_required(c_nom, di_x_w, n_x_w, di_pb_bw, n_lagen)

    # Wenn b_w zu klein ist, wird ein Geometrie-Strafwert generiert
    penalty_bw = max(b_w_erforderlich - b_w, 0)

    # Skalierungsfaktor für die Strafe (muss hoch sein, da Abweichungen im Millimeterbereich liegen)
    penalty_bw_scaled = penalty_bw * 1e8

    #create section
    section = struct_analysis.RibbedConcrete(concrete, reinfsteel, l0, b, b_w, h_f+h_w, h_f, di_xu, s_xu, di_xo, s_xo, di_x_w, n_x_w, di_pb_bw, s_pb_bw, n_pb_bw, n_lagen, phi, c_nom, xi, jnt_srch)

     # create member
    member = struct_analysis.Member1D(section, system, floorstruc, criteria, g2k, qk)
    member.calc_qk_zul_gzt()  # calculate admissible live load

    # define penalty1, if ULS is not fulfilled
    penalty1 = 1e8 *max(member.qk - member.qk_zul_gzt, 0)


    # define penalty2, if SLS1 (deflections) are not fulfilled
    '''if member.mkd_p < member.section.mr_p and abs(member.mkd_n) < abs(member.section.mr_n):
        d1, d2, d3 = [member.w_install - member.w_install_adm, member.w_use - member.w_use_adm,
                      member.w_app - member.w_app_adm]
    else:
        d1, d2, d3 = [member.w_install - member.w_install_adm, member.w_use - member.w_use_adm,
                      member.w_app - member.w_app_adm]
        #d1, d2, d3 = [member.w_install_ger - member.w_install_adm, member.w_use_ger - member.w_use_adm,
        #              member.w_app_ger - member.w_app_adm]'''

    #Berechnung immer für Durchbiegung gerissen
    d1, d2, d3 = [member.w_install_ger - member.w_install_adm, member.w_use_ger - member.w_use_adm,
                      member.w_app_ger - member.w_app_adm]

    penalty2 = 1e8 * max(d1, d2, d3, 0)

    # define penalty3, if SLS2 (vibrations) are not fulfilled
    #pen_a = member.a_ed - member.requirements.a_cd  # Grössenordnung 1e-2
    #pen_w = member.wf_ed - member.requirements.w_f_cdr1 * member.r1  # HBT S. 48. r2 wird gleich 1 gesetzt
    # (Störungen im benachbarten Feld akzeptiert)  # Grössenordnung 1e-5
    #pen_v = member.ve_ed - member.ve_cd  # Grössenordnung 1e-3
    #if member.f1 < member.requirements.f1:
    #    penalty3 = max(pen_a * 1e2, pen_w * 1e5, pen_v * 1e3, 0)
    #else:
    #    penalty3 = max(pen_w * 1e5, pen_v * 1e3, 0)
    penalty3 = 0

    # define penalty4, if fire resistance is not fulfilled
    member.get_fire_resistance()
    penalty4 = 1e5 *max(member.requirements.t_fire-member.fire_resistance, 0)

    # optimize ULS only
    if criterion == "ULS":  # optimize ultimate limit state
        if to_opt == "GWP":
            return member.section.co2*(1+penalty1+ penalty_bw_scaled)
        elif to_opt == "h":
            return member.section.h*(1+penalty1+ penalty_bw_scaled)

    # optimize SLS1 (deflections). Make sure, that also ULS is fulfilled
    elif criterion == "SLS1":  # optimize service limit state (deflections)
        if to_opt == "GWP":
            return member.section.co2*(1+penalty2+ penalty_bw_scaled)
        elif to_opt == "h":
            return member.section.h*(1+penalty2+ penalty_bw_scaled)

    # optimize SLS2 (vibrations). Make sure, that also ULS is fulfilled
    elif criterion == "SLS2":
        if to_opt == "GWP":
            to_minimize = member.section.co2*(1+penalty3+ penalty_bw_scaled)
        elif to_opt == "h":
            to_minimize = member.section.h*(1+penalty3+ penalty_bw_scaled)

    # optimize fire resistance only
    elif criterion == "FIRE":
        if to_opt == "GWP":
            return member.section.co2*(1+penalty4+ penalty_bw_scaled)
        elif to_opt == "h":
            return member.section.h * (1+penalty4+ penalty_bw_scaled)

    # optimize solution, which fulfills all requirements (ULS, SLS1 and SLS2, FIRE)
    elif criterion == "ENV":
        if to_opt == "GWP":
            to_minimize = member.section.co2*(1+penalty1+penalty2+penalty3+penalty4+ penalty_bw_scaled)
        elif to_opt == "h":
            to_minimize = member.section.h*(1+penalty1+penalty2+penalty3+penalty4+ penalty_bw_scaled)
    else:
        to_minimize = 99
        print("criterion " + criterion + " is not defined")
        print("criterion has to be 'ULS', 'SLS1', 'SLS2', 'FIRE' or 'ENV'")
    return to_minimize


#OPTIMIZATION OF WOOD CROSS-SECTIONS-------------------------------------------------------------------

# ----------------------------------------------------------------------------------------------------------------------
# OPTIMIZATION OF RECTANGULAR TIMBER CROSS-SECTIONS
# .......................................................................................................................

available_h = [0.1, 0.12, 0.14, 0.16, 0.18, 0.2, 0.22, 0.24, 0.26, 0.28] #verfügbare Deckenstärke für Brettstapeldecken gemäss Herstellerdaten

# Nachweise, die je Optimierungskriterium erfüllt sein müssen (None = alle aus failed_checks)
CHECKS_PER_CRITERION = {
    "ULS": {"ULS"},
    "SLS1": {"SLS1"},
    "SLS2": {"SLS2"},
    "FIRE": {"FIRE"},
    "ENV": None,
}

def opt_gzt_wd_rqs(member, criterion="ULS", h_max=0.28, max_iter=None, alg=None):
    # Massivholzdecke: alle handelsüblichen Höhen aufsteigend prüfen und die erste (= kleinste) zurückgeben,
    # die alle für 'criterion' relevanten Nachweise erfüllt. Da co2 ~ h (b fix), ist das auch das GWP-Optimum.
    # max_iter und alg werden nicht benötigt (nur für einheitliche Signatur).
    m = member
    relevant = CHECKS_PER_CRITERION.get(criterion)

    for h in sorted(x for x in available_h if x <= h_max):
        section = struct_analysis.RectangularWood(m.section.wood_type, m.section.b, h, m.section.phi)
        test_member = struct_analysis.Member1D(section, m.system, m.floorstruc, m.requirements, m.g2k, m.qk_area)

        failed = failed_checks(test_member)
        if relevant is not None:
            failed = [f for f in failed if f in relevant]
        if not failed:
            return section

    return None  # keine verfügbare Höhe erfüllt die Nachweise -> Aufrufer meldet "no feasible section"



##Otpimierung WD_RIB---------------------------------------------------------------------------------------

# Optimierung durch Berechnung aller handelsüblichen Kombinationen
# Handelsübliche Abmessungen (kategorial) für opt_wd_rib
T_KANDIDATEN_WDRIB = [0.027, 0.04]  # Beplankungsstärken t2 (unten) / t3 (oben)
T2_FIX_WDRIB = 0.027 #Stärke Beplankung unten t2 fix (keine Optimierungsvariable)
BW_KANDIDATEN_WDRIB = [0.1, 0.12, 0.14, 0.16, 0.18, 0.2, 0.22, 0.24]  # Rippenbreite bw
B_KANDIDATEN_WDRIB = [0.625, 0.7]  # Rippenabstand b (Lignum 4.1, Table 433-2)

# Rippenhöhe h: Handelsstärken hängen vom Werkstoff der Rippe ab (Vollholz/BSH "C.." vs. Brettschichtholz "GL..")
H_KANDIDATEN_C = [0.12, 0.14, 0.16, 0.18, 0.2, 0.22, 0.24, 0.26, 0.28, 0.3] #2cm Schritte
H_KANDIDATEN_GL = [0.12, 0.16, 0.2, 0.24, 0.28, 0.32, 0.36, 0.4, 0.44, 0.48, 0.52, 0.56, 0.6, 0.64, 0.68, 0.72, 0.76, 0.8]  # 4 cm Schritte


def opt_wd_rib(m, to_opt="GWP", criterion="ULS", max_iter=None, alg=None, t2=T2_FIX_WDRIB, t3=T_KANDIDATEN_WDRIB[0]):
    # Hohlkasten: alle handelsüblichen Kombinationen (bw, h, b) werden berechnet. Zurückgegeben wird die zulässige
    # Kombination mit minimalem CO2 (to_opt="GWP") bzw. minimaler Höhe (to_opt="h").
    # t2 und t3 sind fix vorgegeben und werden nicht optimiert. Pro Spannweite wird diese Funktion zweimal aufgerufen:
    # einmal je Wert aus T_KANDIDATEN_WDRIB für t3 (Beplankung oben).
    # max_iter und alg werden nicht benötigt (nur für einheitliche Signatur mit den anderen opt_*-Funktionen).

    # Randbedingungen Abmessungen für R60 und Aufbau gemäss Lignum 4.1, Tabelle 433-2, Spalte G:
    # Unten keine Beplankung, aber Hohlraumdämmung und Mindestabmessungen Rippen
    bh = (0.20, 1.0)     # Rippenhöhe zwischen 20 cm (Mindestmass b x h = 120 x 200 für R60) und 1 m
    bbw = (0.12, 0.52)   # Rippenbreite zwischen 12 cm (Mindestmass für R60) und 52 cm
    bt2 = (0.025, 0.16)  # Beplankung unten zwischen 2.5 cm (Mindestmass für R60) und 16 cm
    bt3 = (0.027, 0.16)  # Beplankung oben zwischen 2.7 cm (Mindestmass für R60) und 16 cm
    bb = (0.625, 0.7)    # Rippenabstand b zwischen 0.625 und 0.7 m (Lignum 4.1, Table 433-2)

    # t2, t3 sind fix vorgegeben -> nur prüfen, ob sie innerhalb der Randbedingungen liegen
    if not (bt2[0] <= t2 <= bt2[1] and bt3[0] <= t3 <= bt3[1]):
        return None

    l0 = m.li_max
    ti1, ti2, ti3 = m.section.wood_type_1, m.section.wood_type_2, m.section.wood_type_3

    # Handelsübliche Kandidaten auf die Randbedingungen (R60, Lignum 4.1) einschränken
    bw_kandidaten = [x for x in BW_KANDIDATEN_WDRIB if bbw[0] <= x <= bbw[1]]
    b_kandidaten = [x for x in B_KANDIDATEN_WDRIB if bb[0] <= x <= bb[1]]

    # Höhenkandidaten in Abhängigkeit vom Werkstoff der Rippe (wood_type_1):
    # mech_prop ist z.B. "'C24'" oder "'GL24h'" (inkl. Anführungszeichen aus der DB-Abfrage)
    mech_prop_1 = ti1.mech_prop.strip("'\"")
    h_kandidaten_full = H_KANDIDATEN_GL if mech_prop_1.startswith("GL") else H_KANDIDATEN_C
    h_kandidaten = [x for x in h_kandidaten_full if bh[0] <= x <= bh[1]]

    if not (bw_kandidaten and b_kandidaten and h_kandidaten):
        # keine handelsübliche Kombination innerhalb der Randbedingungen (R60) verfügbar
        return None

    # Nachweise, die für das gewählte Kriterium erfüllt sein müssen (None = alle Nachweise aus failed_checks)
    relevant = CHECKS_PER_CRITERION.get(criterion)

    best_section, best_key = None, None

    # alle Kombinationen berechnen
    for bw, h, b in itertools.product(bw_kandidaten, h_kandidaten, b_kandidaten):
        section = struct_analysis.RibWood(ti1, ti2, ti3, l0, bw, h, b, t2, t3)
        test_member = struct_analysis.Member1D(section, m.system, m.floorstruc, m.requirements, m.g2k, m.qk_area)

        # gleiche Nachweise wie bei der Auswertung im Aufrufer (failed_checks)
        failed = failed_checks(test_member)
        if relevant is not None:
            failed = [f for f in failed if f in relevant]
        if failed:
            continue  # Kombination unzulässig

        # Zielgrösse; bei Gleichstand entscheidet die jeweils andere Grösse
        key = (section.co2, section.h) if to_opt == "GWP" else (section.h, section.co2)
        if best_key is None or key < best_key:
            best_section, best_key = section, key

    return best_section  # None -> keine zulässige Kombination, Aufrufer meldet "no feasible section"






'''
#ALT: Optimierung mit TPE
# Handelsübliche Abmessungen (kategorial) für opt_wd_rib
T_KANDIDATEN_WDRIB = [0.027, 0.04]  # Beplankungsstärken t2 (unten) / t3 (oben)
T2_FIX_WDRIB = 0.027 #Stärke Beplankung unten t2 fix (keine Optimierungsvariable)
BW_KANDIDATEN_WDRIB = [0.1, 0.12, 0.14, 0.16, 0.18, 0.2, 0.22, 0.24]  # Rippenbreite bw
B_KANDIDATEN_WDRIB = [0.625, 0.7]  # Rippenabstand b (Lignum 4.1, Table 433-2)

# Rippenhöhe h: Handelsstärken hängen vom Werkstoff der Rippe ab (Vollholz/BSH "C.." vs. Brettschichtholz "GL..")
H_KANDIDATEN_C = [0.12, 0.14, 0.16, 0.18, 0.2, 0.22, 0.24, 0.26, 0.28, 0.3] #2cm Schritte
H_KANDIDATEN_GL = [0.12, 0.16, 0.2, 0.24, 0.28, 0.32, 0.36, 0.4, 0.44, 0.48, 0.52, 0.56, 0.6, 0.64, 0.68, 0.72, 0.76, 0.8]  # 4 cm Schritte

# outer function for finding optimal wooden rib cross-section
def opt_wd_rib(m, to_opt="GWP", criterion="ULS", max_iter=100, alg="TPE", t2=T2_FIX_WDRIB, t3=T_KANDIDATEN_WDRIB[0]):
    #t2 und t3 sind fix vorgegeben und werden nicht optimiert. Pro Spannweite wird diese Funktion zweimal aufgerufen: einmal je Wert aus T_KANDIDATEN_WDRIB für t3 (Beplankung oben)
    # definition of initial values for variables, which are going to be optimized
    h0 = m.section.h
    bw0 = m.section.bw
    b0 = m.section.b

    # define bounds of variables
    # Randbedingungen Abmessungen für R60 und Aufbau gemäss Lignum 4.1, Tabelle 433-2, Spalte G: Unten keine Beplankung, aber Hohlraumdämmung und Mindestabmessungen Rippen
    bh = (0.20, 1.0)  # height of rib between 20 cm and 1 m(minimal requirement b x h = 120 x 200 for R60 according to Lignum 4.1, Table 433-2, Column G) and 200 cm
    bbw = (0.12, 0.52)  # width of rib between 12 cm and 52 cm (minimal requirement b x h = 120 x 200 for R60 according to Lignum 4.1, Table 433-2, Column G) and 52 cm
    bt2 = (0.025, 0.16)  # hight of lower sheating between 2.5 cm (minimal requirement for R60 according to Lignum 4.1, Table 433-2, Column G) and 16 cm
    bt3 = (0.027, 0.16)  # hight of lower sheating between 2.7 cm (minimal requirement for R60 according to Lignum 4.1, Table 433-2, Column G)
    bb = (0.625, 0.7) #Rippenabstand b zwischen 0.625 und 0.7 m (Lignum4.1, Table 433-2)

    #t2, t3 sind fix vorgegeben -> nur noch prüfen, ob sie innerhlab der Randbedingung liegen
    if not (bt2[0] <= t2 <= bt2[1] and bt3[0] <= t3 <= bt3[1]):
        return None

    # definition of fixed values of cross-section
    l0 = m.li_max

    ti1, ti2, ti3 = m.section.wood_type_1, m.section.wood_type_2, m.section.wood_type_3

    # Handelsübliche Kandidaten auf die Randbedingungen (R60, Lignum 4.1) einschränken
    bw_kandidaten = [x for x in BW_KANDIDATEN_WDRIB if bbw[0] <= x <= bbw[1]]
    b_kandidaten = [x for x in B_KANDIDATEN_WDRIB if bb[0] <= x <= bb[1]]

    # Höhenkandidaten und h_max in Abhängigkeit vom Werkstoff der Rippe (wood_type_1) bestimmen:
    # mech_prop ist z.B. "'C24'" oder "'GL24h'" (inkl. Anführungszeichen aus der DB-Abfrage)
    mech_prop_1 = ti1.mech_prop.strip("'\"")
    if mech_prop_1.startswith("GL"):
        h_kandidaten_full = H_KANDIDATEN_GL
    else:
        h_kandidaten_full = H_KANDIDATEN_C
    h_kandidaten = [x for x in h_kandidaten_full if bh[0] <= x <= bh[1]]
    h_max = max(h_kandidaten) if h_kandidaten else bh[1]

    if not (bw_kandidaten and b_kandidaten and h_kandidaten):
        # keine handelsübliche Kombination innerhalb der Randbedingungen (R60) verfügbar
        return None

    add_arg = [m.system, ti1, ti2, ti3, l0, m.floorstruc, m.requirements, to_opt, criterion, m.g2k, m.qk_area]

    # TPE-Algorithmus mit Optuna
    def objective(trial):

        bw = trial.suggest_categorical("bw", bw_kandidaten)
        h = trial.suggest_categorical("h", h_kandidaten)
        b = trial.suggest_categorical("b", b_kandidaten)

        try:
            return wd_rib_rqs([bw, h, t2, t3, b], add_arg)
        except Exception:
            return 1e20

    study = optuna.create_study(
        direction="minimize",
        sampler=optuna.samplers.TPESampler(seed=42)
    )

    # Startpunkt: nächstgelegene verfügbare Werte zum ursprünglichen Querschnitt
    study.enqueue_trial({
        "bw": min(bw_kandidaten, key=lambda x: abs(x - bw0)),
        "h": min(h_kandidaten, key=lambda x: abs(x - h0)),
        "b": min(b_kandidaten, key=lambda x: abs(x - b0)),
    })

    study.optimize(
        objective,
        n_trials=max_iter
    )

    bw = study.best_params["bw"]
    h = study.best_params["h"]
    b = study.best_params["b"]

    optimized_section = struct_analysis.RibWood(ti1, ti2, ti3, l0, bw, h, b, t2, t3)

    # Check feasibility (analog opt_gzt_wd_rqs): wd_rib_rqs returns the pure objective value (co2 or h) only if all
    # penalties of the criterion are 0. If even the best candidate violates a requirement, no section is returned.
    best_value = wd_rib_rqs([bw, h, t2, t3, b], add_arg)
    pure_value = optimized_section.co2 if to_opt == "GWP" else optimized_section.h
    if best_value > pure_value * (1 + 1e-9):
        return None

    return optimized_section

#inner function for optimizing wood sections for criteria ULS or SLS in terms of GWP or height
def wd_rib_rqs(var, add_arg):
    bw, h, t2, t3, b = var
    system = add_arg[0]
    timber1 = add_arg[1]
    timber2 = add_arg[2]
    timber3 = add_arg[3]
    l0 = add_arg[4]
    floorstruc = add_arg[5]
    criteria = add_arg[6]
    to_opt = add_arg[7]
    criterion = add_arg[8]
    g2k = add_arg[9]
    qk = add_arg[10]

    # create section
    section = struct_analysis.RibWood(timber1, timber2, timber3, l0, bw, h, b, t2, t3)

    # create member
    member = struct_analysis.Member1D(section, system, floorstruc, criteria, g2k, qk)
    member.calc_qk_zul_gzt()  # calculate admissible live load
    # define penalty1, if ULS is not fulfilled
    penalty1 = max(member.qk - member.qk_zul_gzt, 0)

    # define penalty2, if SLS1 (deflections) are not fulfilled
    d1, d2, d3 = [member.w_install - member.w_install_adm, member.w_use - member.w_use_adm,
                      member.w_app - member.w_app_adm]
    penalty2 = 1e5 * max(d1, d2, d3, 0)

    # define penalty3, if SLS2 (vibrations) are not fulfilled
    pen_a = member.a_ed - member.requirements.a_cd  # Grössenordnung 1e-2
    pen_w = member.wf_ed - member.requirements.w_f_cdr1 * member.r1  # HBT S. 48. r2 wird gleich 1 gesetzt
    # (Störungen im benachbarten Feld akzeptiert)  # Grössenordnung 1e-5
    pen_v = member.ve_ed - member.ve_cd  # Grössenordnung 1e-3
    if member.f1 < member.requirements.f1:
        penalty3 = max(pen_a * 1e2, pen_w * 1e5, pen_v * 1e3, 0)
    else:
        penalty3 = max(pen_w * 1e5, pen_v * 1e3, 0)

    # define penalty4, if fire resistance is not fulfilled
    member.get_fire_resistance()
    penalty4 = 0#max(member.requirements.t_fire - member.fire_resistance, 0)

    # optimize ULS only
    if criterion == "ULS":  # optimize ultimate limit state
        if to_opt == "GWP":
            return member.section.co2 * (1 + penalty1)
        elif to_opt == "h":
            return member.section.h * (1 + penalty1)

    # optimize SLS1 (deflections). Make sure, that also ULS is fulfilled
    elif criterion == "SLS1":  # optimize service limit state (deflections)
        if to_opt == "GWP":
            return member.section.co2 * (1 + penalty2)
        elif to_opt == "h":
            return member.section.h * (1 + penalty2)

    # optimize SLS2 (vibrations). Make sure, that also ULS is fulfilled
    elif criterion == "SLS2":
        if to_opt == "GWP":
            to_minimize = member.section.co2 * (1 + penalty3)
        elif to_opt == "h":
            to_minimize = member.section.h * (1 + penalty3)

    # optimize fire resistance only
    elif criterion == "FIRE":
        if to_opt == "GWP":
            return member.section.co2 * (1 + penalty4)
        elif to_opt == "h":
            return member.section.h * (1 + penalty4)

    # optimize solution, which fulfills all requirements (ULS, SLS1 and SLS2, FIRE)
    elif criterion == "ENV":
        if to_opt == "GWP":
            to_minimize = member.section.co2 * (1 + penalty1 + penalty2 + penalty3 + penalty4)
        elif to_opt == "h":
            to_minimize = member.section.h * (1 + penalty1 + penalty2 + penalty3 + penalty4)
    else:
        to_minimize = 99
        print("criterion " + criterion + " is not defined")
        print("criterion has to be 'ULS', 'SLS1', 'SLS2', 'FIRE' or 'ENV'")
    return to_minimize
'''





# ----------------------------------------------------------------------------------------------------------------------
# VERIFICATIONS OF AN OPTIMIZED MEMBER
# ----------------------------------------------------------------------------------------------------------------------
def failed_checks(member):
    # returns the names of all verifications the member does not fulfill ([] -> all fulfilled), whatever criterion it
    # was optimized for. 1D and 2D. Same rules as the objective functions, so only the active verifications count:
    # SLS2 only for wood (switched off for concrete), FIRE not for wd_rib (switched off in wd_rib_rqs)
    section = member.section
    section_type = section.section_type
    failed = []

    member.calc_qk_zul_gzt()
    if member.qk > member.qk_zul_gzt:
        failed.append("ULS")

    # deflections: wood uncracked, rc_rib always cracked, rc_rec uncracked only if field and support are uncracked
    if section_type == "rc_rec":
        cracked = not (member.mkd_p < section.mr_p and abs(member.mkd_n) < abs(section.mr_n))
    else:
        cracked = section_type == "rc_rib"
    if cracked:
        d1, d2, d3 = [member.w_install_ger - member.w_install_adm, member.w_use_ger - member.w_use_adm,
                      member.w_app_ger - member.w_app_adm]
    else:
        d1, d2, d3 = [member.w_install - member.w_install_adm, member.w_use - member.w_use_adm,
                      member.w_app - member.w_app_adm]
    if max(d1, d2, d3) > 0:
        failed.append("SLS1")

    if section_type in ("wd_rec", "wd_rib"):
        pen_a = member.a_ed - member.requirements.a_cd
        pen_w = member.wf_ed - member.requirements.w_f_cdr1 * member.r1
        pen_v = member.ve_ed - member.ve_cd
        if member.f1 < member.requirements.f1:
            pen_sls2 = max(pen_a, pen_w, pen_v)
        else:
            pen_sls2 = max(pen_w, pen_v)
        if pen_sls2 > 0:
            failed.append("SLS2")

    if section_type != "wd_rib":
        member.get_fire_resistance()
        if member.requirements.t_fire > member.fire_resistance:
            failed.append("FIRE")

    if section_type == "rc_rib":
        di_x_w, n_x_w, n_lagen = section.bw_r
        if section.b_w < rib_b_w_required(section.c_nom, di_x_w, n_x_w, section.bw_bg_r[0], n_lagen):
            failed.append("b_w")
    return failed


#-----------------------------------------------------------------------------------------------------------------------
# function for returning optimal section for defined QS-type, system, requirements, loads, criterion and type of optimum
def get_optimized_section(member, criterion, to_opt, max_iter, alg, fixed_params=None):
    # fixed_params: optional dict of section-specific parameters that are held fixed (not optimized),
    # e.g. {"t3": 0.04} for wd_rib. Forwarded as **kwargs to the matching opt_* function, which must
    # accept a keyword of that name; unused for section types whose opt_* function doesn't declare it.
    fixed_params = fixed_params or {}
    if member.section.section_type == "rc_rec":
        # available to_opt arguments: "GWP", "h"
        # available criterion arguments: "ULS", "SLS1", "SLS2"
        return opt_rc_rec(member, to_opt, criterion, max_iter, 0.2, alg, **fixed_params)
    elif member.section.section_type == "wd_rec":
        # available criterion arguments: "ULS", "SLS1", "SLS2"
        return opt_gzt_wd_rqs(member, criterion=criterion, **fixed_params)
    elif member.section.section_type == "rc_rib":
        # available to_opt arguments: "GWP", "h"
        # available criterion arguments: "ULS", "SLS1", "SLS2"
        return opt_rc_rib(member, to_opt, criterion, max_iter, alg, **fixed_params)
    elif member.section.section_type == "wd_rib":
        # available to_opt arguments: "GWP", "h"
        # available criterion arguments: "ULS", "SLS1", "SLS2"
        return opt_wd_rib(member, to_opt, criterion, max_iter, **fixed_params)
    else:
        print("There is no optimization for the section type " + member.section.section_type + " available!")
        return member.section
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# OPTIMIZATION OF CROSS-SECTIONS REGARDING PERFORMANCE WITHIN A DEFINED GWP BUDGET
# ----------------------------------------------------------------------------------------------------------------------
def get_opt_sec(section, gwp_budget):
    if section.section_type == "wd_rec":
        # outer function for finding optimal wooden rectangular cross-section
        h_0 = section.h
        bnds = [(0.02, 10.0)]
        minimal_h = minimize(wd_rec_crsc, h_0, args=[section, gwp_budget], bounds=bnds, method='Powell')
        h_opt = minimal_h.x[0]
        opt_section = struct_analysis.RectangularWood(section.wood_type, section.b, h_opt)

        return opt_section

    elif section.section_type == "rc_rec":
        # get initial values
        h_0 = section.h
        di_xu0 = section.bw[0][0]
        var0 = [h_0, di_xu0]

        # define bounds of variables
        bh = (0.08, 2.0)  # height between 8 cm and 2.0 m
        bdi_xu = (0.008, 0.04)  # diameter of rebars between 6 mm and 40 mm
        bounds = [bh, bdi_xu]

        # definition of fixed values of cross-section
        b = section.b
        s_xu, di_xo, s_xo = section.bw[0][1], section.bw[1][0], section.bw[1][1]
        di_bw, s_bw, n_bw = section.bw_bg[0], section.bw_bg[1], section.bw_bg[2]
        phi, c_nom, xi, jnt_srch = section.phi, section.c_nom, section.xi, section.joint_surcharge
        co, st = section.concrete_type, section.rebar_type
        add_arg = [co, st, b, s_xu, di_xo, s_xo, di_bw, s_bw, n_bw, phi, c_nom, xi, jnt_srch, gwp_budget]

        # optimize with basinhopping algorithm with bounds also implemented on both levels (inner and outer):
        bounded_step = RandomDisplacementBounds(np.array([b[0] for b in bounds]), np.array([b[1] for b in bounds]))
        opt = basinhopping(rc_rec_crsc, var0, minimizer_kwargs={"args": (add_arg,), "bounds": bounds,
                                                                "method": "Powell"},
                           take_step=bounded_step)
        h, di_xu = opt.x
        opt_section = struct_analysis.RectangularConcrete(co, st, b, h, di_xu, s_xu, di_xo, s_xo, di_bw, s_bw,
                                                                n_bw, phi, c_nom, xi, jnt_srch)


        return opt_section

    elif section.section_type == "rc_rib":
        # get initial values
        h_0 = section.h
        di_xu0 = section.bw[0][0]
        b_w0 = section.b_w
        b0 = section.b
        var0 = [h_0, di_xu0, b_w0, b0]

        # define bounds of variables
        bh = (0.08, 1)  # height between 8 cm and 1.0 m #TODO Bounds anpassen!!
        bdi_x_w = (0.008, 0.04)  # diameter of rebars between 8 mm and 40 mm
        bb_w = (0.12, 0.4)  # rib width between 12 and 60 cm
        bb = (1, 1.5)  # rib spacing between 0.5 and 2.5 m
        bounds = [bh, bdi_x_w, bb_w, bb]


        # definition of fixed values of cross-section
        l0 = section.li_max
        h_f = section.h_f
        di_xu, s_xu, di_xo, s_xo = section.bw[0][0], section.bw[0][1], section.bw[1][0], section.bw[1][1]
        di_pb_bw, s_pb_bw, n_pb_bw = section.bw_bg[0], section.bw_bg[1], section.bw_bg[2]
        n_x_w = section.bw_r[1]
        phi, c_nom, xi, jnt_srch = section.phi, section.c_nom, section.xi, section.joint_surcharge
        co, st = section.concrete_type, section.rebar_type
        add_arg = [co, st, l0, h_f, di_xu, s_xu, di_xo, s_xo, n_x_w, di_pb_bw, s_pb_bw, n_pb_bw, phi, c_nom, xi, jnt_srch, gwp_budget]

        # optimize with basinhopping algorithm with bounds also implemented on both levels (inner and outer):
        bounded_step = RandomDisplacementBounds(np.array([b[0] for b in bounds]), np.array([b[1] for b in bounds]))
        opt = basinhopping(rc_rib_crsc, var0, minimizer_kwargs={"args": (add_arg,), "bounds": bounds,
                                                                "method": "Powell"},
                           take_step=bounded_step)
        h, di_x_w, b_w, b = opt.x
        opt_section = struct_analysis.RibbedConcrete(co, st, l0, b, b_w, h, h_f, di_xu, s_xu, di_xo, s_xo, di_x_w, n_x_w, di_pb_bw, s_pb_bw, n_pb_bw, phi, c_nom, xi, jnt_srch)
        return opt_section

    elif section.section_type == "wd_rib":
        # get initial values
        h_0 = section.h
        b_0 = section.b
        var0 = [h_0, b_0]
        print("wd-rib not yet defined for this plot")

## XXXXXXXXXXX neuen Querschnittstyp für optimierung vorbereiten. Für mehrere parameter: basinhopping methode.

    else:
        print("no optimization for section type " + section.section_type + " is defined yet within method get_opt_sec")
        return section

# inner function used for optimizing rectangular wooden section in terms of maximal bending moment and within gwp_budget
def wd_rec_crsc(h, args):
    s, gwp_budget = args
    section_updated = struct_analysis.RectangularWood(s.wood_type, s.b, h)
    penalty = 1e6*max(section_updated.co2-gwp_budget, 0)
    to_minimize = penalty - section_updated.mu_max
    return to_minimize

# inner function for optimizing reinforced concrete section in terms of maximal bending moment and within gwp_budget
def rc_rec_crsc(var, add_arg):
    h, di_xu = var
    concrete = add_arg[0]
    reinfsteel = add_arg[1]
    b = add_arg[2]
    s_xu, di_xo, s_xo = add_arg[3:6]
    di_bw, s_bw, n_bw = add_arg[6:9]
    phi, c_nom, xi, jnt_srch = add_arg[9:13]
    gwp_budget = add_arg[13]
    section_updated = struct_analysis.RectangularConcrete(concrete, reinfsteel, b, h, di_xu, s_xu, di_xo, s_xo, di_bw,
                                                          s_bw, n_bw, phi, c_nom, xi, jnt_srch)
    penalty = 1e6*max(section_updated.co2-gwp_budget, 0)
    to_minimize = penalty - section_updated.mu_max
    return to_minimize

def rc_rib_crsc(var, add_arg):
    h, di_x_w, b_w, b = var
    concrete = add_arg[0]
    reinfsteel = add_arg[1]
    l0 = add_arg[2]
    h_f = add_arg[3]
    di_xu, s_xu, di_xo, s_xo, n_x_w, di_pb_bw, s_pb_bw, n_pb_bw = add_arg[4:12]
    phi, c_nom, xi, jnt_srch = add_arg[12:16]
    gwp_budget = add_arg[16]
    section_updated = struct_analysis.RibbedConcrete(concrete, reinfsteel, l0, b, b_w, h, h_f, di_xu, s_xu, di_xo, s_xo, di_x_w, n_x_w, di_pb_bw, s_pb_bw, n_pb_bw, phi, c_nom, xi, jnt_srch)
    penalty = 1e6*max(section_updated.co2-gwp_budget, 0)
    to_minimize = penalty - section_updated.mu_max
    return to_minimize

## XXXXXXXXXXX neue funktion (returnwert wird minimiert)

