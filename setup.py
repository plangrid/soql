#!/usr/bin/env python
from setuptools import setup, find_packages


if __name__ == '__main__':
    setup(
        name='soql',
        version='1.0.1',
        author='Barak Alon',
        author_email='barak.s.alon@gmail.com',
        description='Models and query generator for Salesforce Object Query Language (SOQL)',
        long_description=open('README.rst').read(),
        keywords=['salesforce', 'soql', 'salesforce.com'],
        license='MIT',
        packages=find_packages(exclude=('test*')),
        install_requires=[
            'python-dateutil',
            'six',
        ],
        zip_safe=True,
        url='https://github.com/plangrid/soql',
        classifiers=[
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Topic :: Software Development :: Libraries :: Python Modules',
        ]
    )
