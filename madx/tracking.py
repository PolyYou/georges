import os, re, io
import pandas as pd
from .. import beamline
from .. import beam
from .madx import Madx

MADX_TRACKING_SKIP_ROWS = 54
PTC_TRACKING_SKIP_ROWS = 9


class TrackException(Exception):
    """Exception raised for errors in the Track module."""

    def __init__(self, m):
        self.message = m


def read_tracking(file):
    """Read a PTC Tracking 'one' file to a dataframe."""

    def process_data_lines(lines):
        return pd.read_csv(io.StringIO("\n".join(lines)),
                           names=['NUMBER', 'TURN', 'X', 'PX', 'Y', 'PY', 'T', 'PT', 'S', 'E'],
                           delim_whitespace=True)

    regex_header = re.compile("^#segment\s[\d\s]*\s(.*)$")
    data = {}
    collect_particles = False
    location = None
    for line in open(file):
        if line.startswith("#segment"):
            if collect_particles:
                # Process previous data collection before moving on to the next
                data[location] = process_data_lines(tmp)
            location = re.findall(regex_header, line)[0].strip()
            tmp = []
            collect_particles = True
        elif collect_particles:
            tmp.append(line) if tmp is not None else None
    if collect_particles:
        # Process previous data collection
        data[location] = process_data_lines(tmp)
    df = pd.DataFrame.from_dict(
        {k.upper(): beam.Beam(v[['X', 'PX', 'Y', 'PY', 'PT']]) for k, v in data.items()}, orient='index'
    ).rename(columns={0: "BEAM"})
    df.index.name = 'NAME'
    return df


def track(**kwargs):
    """Compute the distribution of the beam as it propagates through the beamline..
    :param kwargs: parameters are:
        - line: the beamline on which twiss will be run
        - context: the associated context on which MAD-X is run
    """
    # Process arguments
    line = kwargs.get('line', None)
    b = kwargs.get('beam', None)
    if line is None or b is None:
        raise TrackException("Beamline, Beam and MAD-X objects need to be defined.")
    m = Madx(beamlines=[line])

    # Create a new beamline to include the results
    line_tracking = line.line.copy()

    # Run MAD-X
    m.beam(line.name)
    m.track(b.distribution,
            line,
            ptc_params=kwargs.get('ptc_params', {}),
            ptc=kwargs.get('ptc', True),
            misalignment=kwargs.get('misalignment', False),
            start=kwargs.get('start', False)
            )
    errors = m.run(**kwargs).fatals
    if kwargs.get("debug", False):
        print(m.raw_input)
        print(m.input)
    if len(errors) > 0:
        print(errors)
        raise TrackException("MAD-X ended with fatal error.")
    if kwargs.get('ptc'):
        madx_track = read_tracking(os.path.join(".", 'ptctrackone.tfs'))
    else:
        madx_track = read_tracking(os.path.join(".", 'tracking.outxone'))
    line_tracking = line_tracking.merge(madx_track, left_index=True, right_index=True, how='left')
    return beamline.Beamline(line_tracking)

