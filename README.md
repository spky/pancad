# pancad

## Overview

pancad is a CAD (Computer-Aided Design) file translator. It is intended to 
enable the sharing of geometry and design information **independent of 
software application**. PanCAD's name is inspired by [Pandoc][1], which is an 
unrelated but similar software application that can convert documents 
from one file type to another.

## How to get it

The source code is hosted on [GitHub][2].

Binary installers for the latest release version are available on the
[Python Package Index (PyPI)][3]

Install using pip:

```sh
pip install pancad
```

## License

2025. This work has been marked as dedicated to the public domain.
See [CC0-1.0][4]

## Dependencies

- [NumPy][5] - Used for matrix operations and numerical functions.
- [quaternion][6] - Used for pesky quaternion defined coordinate systems.
- [SciPy][7] - Used by quaternion.

<!-- References -->

[1]: https://pandoc.org/
[2]: https://github.com/spky/pancad
[3]: https://pypi.org/project/pancad/
[4]: https://creativecommons.org/publicdomain/zero/1.0/
[5]: https://numpy.org/
[6]: https://quaternion.readthedocs.io/en/latest/
[7]: https://scipy.org/