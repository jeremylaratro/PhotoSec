from setuptools import setup

setup(
    name='PhotoSecUtils',
    version='0.3.0',
    packages=['PhotoSec'],
    url='https://github.com/jeremylaratro/PhotoSec.git',
    license='GPL-3.0-only',
    author='Jeremy Laratro',
    author_email='jeremylaratro@gmail.com',
    description='Security/Privacy oriented Python script focused on metadata removal and analysis',
    install_requires=['exif>=1.3.5,<2.0', 'plum-py>=0.8.2,<1.0'],
    entry_points={
        'console_scripts': ['photosec=photoutils:start'],
    },
    python_requires='>=3.8',
)
