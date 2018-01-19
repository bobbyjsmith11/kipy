from setuptools import find_packages, setup

def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='kipy',
      version="0.1",
      description="added functionality for KiCAD",
      long_desription=readme(),
      classifiers=[
          'Development Status :: Alpha ::',
          'License :: OSI Approved :: MIT',
          'Programming Language :: Python 3.5',
      ],
      keywords='KiCAD',
      url="http://github.com/bobbyjsmith11/kipy",
      author="Bobby Smith",
      author_email="bobbyjsmith11@gmail.com",
      license="MIT",
      packages=["kipy"],
      install_requires=[
      ],
      test_suit='nose.collector',
      test_requires=['nose'],
      zip_safe=False
      )
