# Testing Documentation

We have two files with tests of our code

- `test_web.py`: tests functionality of functions in `web.py`. Uses Pythons's `pytest` module. Note the important limitation of needing at least Python 3.10, else this will just refuse to work.
- `src/Tests.py`: tests functionality of functions in `Database.py`. Uses Python's `unittest` module. In order to run this, run the following command: `python -m unittest src/Tests.py`.

Note that we have both mock object testing in `test_web.py` and fuzz testing in the `src/Tests.py`, so advacned testing approaches are used.