from setuptools import setup

import src


setup(
    name=src.__name__,
    version=src.__version__,
    author=src.__author__,
    author_email=src.__email__,
    description=src.__doc__.replace('\n', ' ').strip(),
    license='GPL-3.0+',
    url='https://github.com/chessking94/Utilities_Python',
    python_requires='>=3.10',
    packages=['Utilities_Python'],
    package_dir={'Utilities_Python': 'src'},
    test_suite='test',
    install_requires=[
        'pandas==3.0.1',
        'requests==2.32.5',
        'SQLAlchemy==2.0.47'
    ]
)
