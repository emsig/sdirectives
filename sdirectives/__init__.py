from datetime import datetime as _dt
from sdirectives.sdirectives import PlotAndSaveEveryIteration  # NQA

try:
    from sdirectives.version import version as __version__
except ImportError:
    __version__ = 'unknown-'+_dt.today().strftime('%Y%m%d')
