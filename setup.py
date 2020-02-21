from numpy.distutils.core import Extension

ext1 = Extension(name = 'pcmin',
                 sources = ['pcmin.f'])


if __name__ == "__main__":
    from numpy.distutils.core import setup
    setup(name = 'pcmin',
          description       = "Python wrapper for potential intensity calculation",
          author            = "Craig Arthur",
          author_email      = "craig.arthur@ga.gov.au",
          ext_modules = [ext1]
          )