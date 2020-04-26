import os
from setuptools import setup, find_packages

install_requires = [
    'requests[security]>=2.23.0,<3',
    'pyvmomi>=6.5,<=7',
    'python-decouple',
    'furl',
    'click',
    'typical>=2.0,<3.0',

    'pytest>=5.4.1',  # for mce_django_app.pytest.plugin
]

tests_requires = [
    'pytest>=5.4.1',
    'bandit',
    'flake8',
    'coverage',
    'pytest-cov',
    'pytest-pep8',
    'pytest-flake8',
    'black',
    'freezegun',
]

dev_requires = [
    'pylint',
    'ipython',
    'autopep8',
    'twine',
    'wheel'
]

doc_requires = [
    'Sphinx',
    'sphinx_rtd_theme',
    'sphinx-click',
    'sphinx-autodoc-typehints'
]

extras_requires = {
    'tests': tests_requires,
    'dev': dev_requires,
    'doc': doc_requires,
}

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='mce-lib-vsphere',
    version="0.1.0",
    description='Inventory library for VMware (Vsphere Release)',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/multi-cloud-explorer/mce-lib-vsphere.git',
    packages=find_packages(exclude=("tests",)),
    include_package_data=True, 
    tests_require=tests_requires,
    install_requires=install_requires,
    extras_require=extras_requires,
    test_suite='tests',
    zip_safe=False,
    author='Stephane RAULT',
    author_email="stephane.rault@radicalspam.org",
    python_requires='>=3.7',
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
    ],
    entry_points={
        #'console_scripts': [
        #    'mce-vsphere = mce_lib_vsphere.cli:main',
        #],
    }
)

