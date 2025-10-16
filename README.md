# pancad

## Overview

pancad is a CAD (Computer-Aided Design) file translator. It is intended to 
enable the sharing of geometry and design information **independent of 
software application**. PanCAD's name is inspired by [Pandoc][1], which is an 
unrelated but similar software application that can convert documents 
from one file type to another.

## How to get it

The source code is hosted on GitHub at: https://github.com/spky/pancad

Binary installers for the latest release version are available at the
[Python Package Index (PyPI)][5]

```sh
# PyPI
pip install pancad
```

## License

2025. This work has been marked as dedicated to the public domain.
See [CC0-1.0][6]

## Dependencies

- [NumPy][2] - Used for matrix multiplication and mathematical functions for 
those arrays.
- [quaternion][3] - Used for pesky quaternion defined coordinate systems.
- [SciPy][4] - Used by quaternion.

<!-- References -->

[1]: https://pandoc.org/
[2]: https://numpy.org/
[3]: https://quaternion.readthedocs.io/en/latest/
[4]: https://scipy.org/
[5]: https://pypi.org/
[6]: https://creativecommons.org/publicdomain/zero/1.0/