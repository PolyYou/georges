import numpy as np


def scattering_length(**kwargs):
    db = kwargs.get('db')
    material = kwargs['material']
    if material is 'water':
        return 6.0476276613967768
    if material is 'air':
        return 6E-3
    alpha = 0.0072973525664  # Fine structure constant
    avogadro = 6.02e23  # Avogadro's number
    re = 2.817940e-15 * 100  # Classical electron radius (in cm)
    a = db.a(material)
    z = db.z(material)
    rho = db.density(material)
    return 1 / (rho * alpha * avogadro * re**2 * z**2 * (2 * np.log(33219 * (a*z)**(-1/3)) - 1) / a)


class FermiRossi:
    """"""
    @staticmethod
    def t(pv, p1v1, **kwargs):
        es = 15.0  # MeV
        chi_0 = 19.32  # TODO
        return (es/pv) ** 2 * (1/chi_0)


class DifferentialHighland:
    """"""
    @staticmethod
    def t(pv, p1v1, **kwargs):
        db = kwargs.get('db')
        material = kwargs.get('material')
        es = 15.0  # MeV
        return DifferentialHighland.f_dm(l) * (es / pv) ** 2 * (1 / chi_s)

    @staticmethod
    def f_dh(l):
        return 0.970 * (1+(np.log(l)/20.7)) * (1+(np.log(l)/22.7))

    @staticmethod
    def l(x, radiation_length):
        return x / radiation_length


class ICRU:
    """"""
    @staticmethod
    def t(pv, p1v1, **kwargs):
        pass


class ICRUProtons:
    """"""
    @staticmethod
    def t(pv, p1v1, **kwargs):
        db = kwargs.get('db')
        material = kwargs['material']
        es = 15.0  # MeV
        chi_s = scattering_length(material=material, db=db)
        return (es / pv) ** 2 * (1 / chi_s)


class DifferentialMoliere:
    """"""
    @staticmethod
    def t(pv, p1v1, **kwargs):
        db = kwargs.get('db')
        material = kwargs['material']
        es = 15.0  # MeV
        chi_s = scattering_length(material=material, db=db)
        return DifferentialMoliere.f_dm(p1v1, pv) * (es / pv) ** 2 * (1 / chi_s)

    @staticmethod
    def f_dm(p1v1, pv):
        return 0.5244 \
               + 0.1975 * np.log10(1 - (pv / p1v1) ** 2) \
               + 0.2320 * np.log10(pv) \
               - 0.0098 * np.log10(pv) * np.log10(1 - (pv / p1v1) ** 2)
