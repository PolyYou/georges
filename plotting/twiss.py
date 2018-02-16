import numpy as np
from .common import palette, filled_plot


def twiss(ax, bl, **kwargs):
    """Plot the Twiss beam envelopes from a beamline Twiss computation and a context."""
    context = kwargs.get('context', {})
    bl = bl.line

    bl['XMAXMONO'] = np.sqrt(bl['BETX']*context['EMITX'])
    bl['XMAX'] = np.sqrt(bl['XMAXMONO']**2+(context['DPP']*bl['DX'])**2)
    bl['YMAX'] = np.sqrt(bl['BETY']*context['EMITY'])
    p = kwargs.get('plane', None)
    cx = kwargs.get('color', 'X')
    cy = kwargs.get('color', 'Y')
    if p is None:
        filled_plot(ax, bl['S'], 0, -1000 * bl['XMAXMONO'], palette[cx], True, alpha=0.8)
        filled_plot(ax, bl['S'], 0, -1000 * bl['XMAX'], palette[cx], True, alpha=0.4)
        filled_plot(ax, bl['S'], 0, -2 * 1000 * bl['XMAX'], palette[cx], True, alpha=0.2)
        filled_plot(ax, bl['S'], 0, 1000 * bl['YMAX'], palette[cy], True, alpha=0.4)
        filled_plot(ax, bl['S'], 0, 2 * 1000 * bl['YMAX'], palette[cy], True, alpha=0.2)
    elif p == 'X':
        filled_plot(ax, bl['S'], 0, -1000 * bl['XMAXMONO'], palette[cx], True, alpha=0.8)
        filled_plot(ax, bl['S'], 0, -1000 * bl['XMAX'], palette[cx], True, alpha=0.4)
        filled_plot(ax, bl['S'], 0, -2 * 1000 * bl['XMAX'], palette[cx], True, alpha=0.2)
        filled_plot(ax, bl['S'], 0, 1000 * bl['XMAXMONO'], palette[cx], True, alpha=0.8)
        filled_plot(ax, bl['S'], 0, 1000 * bl['XMAX'], palette[cx], True, alpha=0.4)
        filled_plot(ax, bl['S'], 0, 2 * 1000 * bl['XMAX'], palette[cx], True, alpha=0.2)
    else:
        filled_plot(ax, bl['S'], 0, 1000 * bl['YMAX'], palette[cy], True, alpha=0.4)
        filled_plot(ax, bl['S'], 0, 2 * 1000 * bl['YMAX'], palette[cy], True, alpha=0.2)
        filled_plot(ax, bl['S'], 0, -1000 * bl['YMAX'], palette[cy], True, alpha=0.4)
        filled_plot(ax, bl['S'], 0, -2 * 1000 * bl['YMAX'], palette[cy], True, alpha=0.2)


def beta(ax, bl, **kwargs):
    """Plot the Twiss beta functions."""
    if kwargs.get('ptc', False):
        twiss_function_plot(ax, bl, ['BET'])
    else:
        ax.plot(bl.line['S'], bl.line['BETA11'], color=palette['X'])
        ax.plot(bl.line['S'], bl.line['BETA22'], color=palette['Y'])


def alpha(ax, bl, **kwargs):
    """Plot the Twiss alpha functions."""
    if kwargs.get('ptc', False):
        twiss_function_plot(ax, bl, ['ALF'])
    else:
        ax.plot(bl.line['S'], bl.line['ALFA11'], color=palette['X'])
        ax.plot(bl.line['S'], bl.line['ALFA22'], color=palette['Y'])


def dispersion(ax, bl, **kwargs):
    """Plot the dispersion functions."""
    if kwargs.get('ptc', False):
        twiss_function_plot(ax, bl, ['DISP'], ptc=True)
    else:
        # Caution: MAD-X dispersion is affected by relativistic factors
        # See section 1.7.4 of the MAD-X user guide
        ax.plot(bl.line['S'], kwargs.get('beta', 1)*bl.line['DX'], color=palette['X'])
        ax.plot(bl.line['S'], kwargs.get('beta', 1)*bl.line['DY'], color=palette['Y'])


def phase_advance(ax, bl, **kwargs):
    """Plot the phase advance."""
    twiss_function_plot(ax, bl, ['MU'], kwargs.get('ptc', False))


def twiss_function_plot(ax, bl, functions, **kwargs):
    bl = bl.line

    if kwargs.get('ptc', False):
        x = '1'
        y = '3'
    else:
        x = 'X'
        y = 'Y'
    for f in functions:
        ax.plot(bl['S'], bl[f+x], color=palette['X'])
        ax.plot(bl['S'], bl[f+y], color=palette['Y'])
