from setuptools import setup, find_packages
setup(
    name="Todo",
    version="0.1",
    py_modules=['todo'],
    entry_points={
        'console_scripts': ['todo=todo:main'],
    }
)