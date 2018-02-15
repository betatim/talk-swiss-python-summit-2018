from setuptools import setup


setup(name='bikes',
      version='0.0.1',
      description='Zurich bike helpers',
      author='Tim Head',
      author_email='tim@wildtreetech.com',
      license='BSD',
      long_description='Zurich bike helpers',
      packages=['bikes'],
      install_requires=['pandas', 'matplotlib', 'requests']
      )
