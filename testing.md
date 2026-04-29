# Testing Documentation

We have two files with tests of our code

- `test_web.py`: tests functionality of functions in `web.py`. Uses Pythons's `pytest` module. Note the important limitation of needing at least Python 3.10, else this will just refuse to work. To run, run the command `pytest test_web.py`.
- `src/Tests.py`: tests functionality of functions in `Database.py`. Uses Python's `unittest` module. In order to run this, run the following command: `python -m unittest src/Tests.py`.

Note that we have both mock object testing in `test_web.py` and fuzz testing in the `src/Tests.py`, so advacned testing approaches are used.

Coverage here is the two main backend files, `web.py`, `Database.py`. This is where all of our project's functionality comes from. Limitations: mock objects that add junk data to our actual database can cause problems! SO mock objects that put correct data work, struggles with junk.