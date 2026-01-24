"""Setup script for beets-performers plugin."""

from setuptools import setup

setup(
    name='beets-performers',
    version='0.1.0',
    description='Beets plugin to use performer information from MusicBrainz as artist tags',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Beets Community',
    url='https://github.com/justinsalloum/beets-performers',
    license='MIT',
    platforms='ALL',
    packages=['beetsplug'],
    namespace_packages=['beetsplug'],
    install_requires=[
        'beets>=1.6.0',
        'musicbrainzngs>=0.7.1',
    ],
    classifiers=[
        'Topic :: Multimedia :: Sound/Audio',
        'Topic :: Multimedia :: Sound/Audio :: Players :: MP3',
        'License :: OSI Approved :: MIT License',
        'Environment :: Console',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)
