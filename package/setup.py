from setuptools import setup, find_packages

VERSION = '0.0.3'
DESCRIPTION = 'Linter for Open API specification documents'
LONG_DESCRIPTION = 'A yaml linter for opeanpi documents. '

# Setting up
setup(
    name="linter",
    version=VERSION,
    author="BAUHAUS",
    author_email="shubhushan.kattel@bahag.com",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    install_requires=["PyYAML", "python-dotenv"],
    scripts = ["bin/linting"],
    keywords=['python', 'yaml', 'linter'],
    classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ]
)