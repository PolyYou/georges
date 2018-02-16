import os
import pandas as pd
from .. import beamline
from .. import beam
from .g4beamline import G4Beamline
import numpy as np
from .. import physics

G4BEAMLINE_SKIP_ROWS = 3


class TrackException(Exception):
    """Exception raised for errors in the Track module."""

    def __init__(self, m):
        self.message = m


def read_g4beamline_tracking(file):
    """Read a G4Beamline Tracking 'one' file to a dataframe."""

    column_names = ['X', 'Y', 'S', 'PX', 'PY', 'PZ', 't', 'PDGid', 'EventID', 'TrackID', 'ParentID', 'Weight']
    tmp = np.nan
    if os.path.isfile(file):
        data = pd.read_csv(file, skiprows=G4BEAMLINE_SKIP_ROWS, delimiter=' ', header=None, names=column_names) \
                 .query("TrackID == 1 and ParentID == 1")

        if len(data) == 0:
            return tmp
        data['X'] /= 1000
        data['Y'] /= 1000
        data['S'] /= 1000
        data['P'] = np.sqrt(data['PX']**2+data['PY']**2+data['PZ']**2)
        data['PX'] /= data['P']
        data['PY'] /= data['P']

        tmp = beam.Beam(data[['X', 'PX', 'Y', 'PY', 'P']])

    return tmp


def track(**kwargs):
    """Compute the distribution of the beam as it propagates through the beamline..
    :param kwargs: parameters are:
        - line: the beamline on which twiss will be run
        - context: the associated context on which MAD-X is run
    """
    # Process arguments
    line = kwargs.get('line', None)
    b = kwargs.get('beam', None)
    context = kwargs.get('context', None)

    if line is None or b is None or context is None:
        raise TrackException("Beamline, Beam, context and G4Beamline objects need to be defined.")

    g4 = G4Beamline(beamlines=[line], **kwargs)

    # Convert m in mm for G4Beamline and rad in MeV/c
    g4_beam = b.distribution.copy()

    momentum = physics.energy_to_momentum(b.energy)
    g4_beam['X'] *= 1000
    g4_beam['Y'] *= 1000
    g4_beam['Z'] = 0.0
    g4_beam['PX'] *= momentum
    g4_beam['PY'] *= momentum
    g4_beam['PZ'] = np.sqrt(momentum**2 - g4_beam['PX']**2 - g4_beam['PY']**2)
    g4_beam['t'] = 0.0
    g4_beam['PDGid'] = 2212
    g4_beam['EventId'] = np.arange(1, len(b.distribution)+1, 1)
    g4_beam['TrackId'] = 1
    g4_beam['ParentId'] = 1
    g4_beam['Weight'] = 1.0

    # Create a new beamline to include the results
    l = line.line.copy()

    # Run G4Beamline
    g4.track(round(g4_beam, 5))
    errors = g4.run(**kwargs).fatals

    if kwargs.get("debug", False):
        print(g4.raw_input)
        print(g4.input)
    if len(errors) > 0:
        print(errors)
        # raise TrackException("G4Beamline ended with fatal error.")

    # Add columns which contains datas
    l['BEAM'] = l.apply(lambda g: read_g4beamline_tracking('Detector'+g.name+'.txt'), axis=1)
    l.apply(lambda g:
            os.remove('Detector' + g.name + '.txt') if os.path.isfile('Detector' + g.name + '.txt') else None,
            axis=1)

    return beamline.Beamline(l)
