import os
from setuptools import setup
import hyppy

dir = os.path.dirname(os.path.abspath(__file__))
readme = open(os.path.join(dir, 'README.rst')).read()
required = open(os.path.join(dir, 'requirements.txt')).read().splitlines()

setup(name='hyppy',
    version=hyppy.__version__,
    packages=['hyppy'],
    install_requires=required,

    description='HAPI wrapper and tools for the online game Hyperiums',
    long_description=readme,
    author='Ross Masters',
    author_email='ross@rossmasters.com',
    url='https://github.com/Hypex/hyppy.git',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
	'License :: OSI Approved :: MIT License',
	'Operating System :: OS Independent',
	'Programming Language :: Python',
        'Topic :: Games/Entertainment :: Real Time Strategy',
	'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    license='MIT'
)
