from setuptools import setup, find_packages

setup(
    name='mmaictl',
    version='1.0.0',
    packages=find_packages(),
    install_requires=[
        'requests',
        'argcomplete',
    ],
    entry_points={
        'console_scripts': [
            'mmaictl=mmaictl:main',
        ],
    },
)
