from setuptools import setup, find_packages
import os

version = '0.1.0'

here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.md')).read()
except IOError:
    README = ''

setup(name='tgext.debug',
      version=version,
      description="Provides debug handlers for TurboGears2",
      long_description=README,
      classifiers=[
          "Environment :: Web Environment",
          "Topic :: Software Development :: Libraries :: Python Modules",
          "Framework :: TurboGears"
      ],
      keywords='turbogears2',
      author='Evolux Team',
      author_email='dev@evolux.net.br',
      url='https://evolux.net.br',
      license='MIT',
      packages=find_packages(exclude=['test_project']),
      namespace_packages=['tgext'],
      include_package_data=True,
      package_data={'': []},
      zip_safe=False,
      install_requires=[
          "TurboGears2 >= 2.3.9",
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
