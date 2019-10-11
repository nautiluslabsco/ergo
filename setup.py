from distutils.core import setup
setup(
  name = 'ergo', # How you named your package folder (MyLib)
  packages = ['ergo'], # Chose the same as "name"
  version = '0.0.12-alpha', # Start with a small number and increase it with every change you make
  license='MIT', # Chose a license from here: https://help.github.com/articles/licensing-a-repository
  description = 'Simple Microservice Application Runtime Toolkit', # Give a short description about your library
  author = 'Matthew Hansen', # Type in your name
  author_email = 'ergo@mattian.com', # Type in your E-Mail
  url = 'https://github.com/mattian7741/zulu', # Provide either the link to your github or to your website
  download_url = 'https://github.com/mattian7741/zulu/archive/v0.0.12-alpha.tar.gz', # github release url
  keywords = ['EXECUTE', 'MICROSERVICE', 'LAMBDA'], # Keywords that define your package best
  install_requires=[ # dependencies
      ],
  classifiers=[
    'Development Status :: 3 - Alpha', # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
    'Intended Audience :: Developers', # Define that your audience are developers
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License', # Again, pick a license
    'Programming Language :: Python :: 3', #Specify which pyhton versions that you want to support
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
  ],
  entry_points={
    'console_scripts': [
      'ergo=ergo.__main__:run'
    ]
  }

)
