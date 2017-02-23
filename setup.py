from sys import exit, version

from setuptools import setup, find_packages

if version < '3.1.0':
    print("python 3.1 or higher is required")
    exit(1)

description = \
"""
This package can be used to work with NYPL AMI packages.
"""

# for older pythons ...
requirements = []
try:
    import bagit
except:
    requirements.append("bagit")
try:
    import pandas
except:
    requirements.append("pandas")
try:
    import tqdm
except:
    requirements.append("tqdm")


setup(
    name = 'ami_tools',
    version = 0.1,
    description = description,
    url = 'https://github.com/nypl/ami-tools/',
    author = 'Nick Krabbenhoeft',
    author_email = 'nickkrabennhoeft@nypl.org',
    packages = find_packages(exclude = ['bin']),
    scripts = ['bin/create_json_from_excel.py',
               'bin/fix_baginfo.py',
               'bin/repair_bags.py',
               'bin/validate_ami_bags.py',
               'bin/validate_ami_excel.py',
               'bin/validate_bags.py'],
    platforms = ['POSIX'],
    install_requires = ['argparse', 'pandas'],
    classifiers = [
        'Programming Language :: Python :: 3.1',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)
