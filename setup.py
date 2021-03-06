from setuptools import setup

setup(
    name='Grabarz',
    version='1.0',
    long_description=__doc__,
    packages=['grabarz'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Flask-SQLAlchemy',
        'Flask-script',
        'dateutils',
        'decorator',
        'simplejson',
	'imdbpy',
        'pynav',
	'tornado',
	'blinker',
        'mechanoid',
	'pyrocore',
    ]
)
