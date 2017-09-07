import shutil
import jinja2


class SimulatorException(Exception):
    """Exception raised for errors in the Simulator module."""

    def __init__(self, m):
        self.message = m

class Simulator:

    def __init__(self, **kwargs):
        self._input = ""
        self._output = None
        self._warnings = []
        self._fatals = []
        self._context = {}
        self._last_context = None
        self._path = kwargs.get('path', None)
        self._beamlines = kwargs.get('beamlines', None)
        self._fringe = kwargs.get('fringe', False)
        if isinstance(self._beamlines, list):
            map(self._attach, self._beamlines)
        else:
            self._attach(self._beamlines)

    def _get_exec(self):
        if self._path is not None:
            return self._path + self.EXECUTABLE_NAME
        else:
            #if os == UNIX:
            return shutil.which(self.EXECUTABLE_NAME, path=".:/usr/local/bin:/usr/bin:/bin")
            #else os :
            #return ...

    def print_warnings(self):
        """Print warnings from the previous execution run."""
        [print(w) for w in self._warnings]

    @property
    def warnings(self):
        """Return warnings from the previous execution run."""
        return self._warnings

    @property
    def fatals(self):
        """Return fatal errors from the previous execution run."""
        return self._fatals

    @property
    def input(self, **kwargs):
        if self._last_context is None:
            raise SimulatorException("Asking for input but no context yet.")
        return jinja2.Template(self._input).render(self._last_context)

    @property
    def raw_input(self):
        """Return the current raw input."""
        return self._input

    @property
    def output(self):
        """Return the output of the last simulator run."""
        return self._output

    @property
    def beamlines(self):
        """Return the list of beamlines attached to the simulator."""
        return self._beamlines
