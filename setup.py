# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

long_desc = '''
This package is a virtual namespace for openaps.contrib modules.

'''

requires = ['recurrent']

setup(
    name='openaps-contrib',
    version='0.0.15',
    url='http://github.com/openaps/openaps-contrib',
    download_url='http://pypi.python.org/pypi/openaps-contrib',
    license='MIT',
    author='Ben West',
    author_email='bewest+openaps@gmail.com',
    description='openaps contrib namespace package',
    long_description=long_desc,
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Documentation',
        'Topic :: Utilities',
    ],
    platforms='any',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requires,
    namespace_packages=['openapscontrib']
)
