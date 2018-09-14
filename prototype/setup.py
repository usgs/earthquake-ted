from distutils.core import setup
import os.path

setup(name='ted',
      description='USGS Tweet Earthquake Detector',
      author='Mike Hearne, Michelle Guy',
      author_email='mhearne@usgs.gov,mguy@usgs.gov',
      url='http://github.com/usgs/ted',
      packages=['ted'],
      package_data={'ted': os.path.join('*')},
      scripts=['bin/event_trigger'],
      )
