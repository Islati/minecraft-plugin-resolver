from setuptools import setup

setup(
    name='mcresolver',
    version='0.1.0',
    packages=[
        'mcresolver',
        'mcresolver.scripts',
        'mcresolver.utils'
    ],
    package_dir={'mcresolver': 'mcresolver'},
    include_package_data=True,
    url='',
    license='',
    author='Brandon Curtis',
    author_email='bcurtis@artectis.com',
    description="""
    Retrieve your Minecraft plugins, and have them automatically configured; Minimizing the amount of time it takes
    to configure and deploy your server!
        """,
    entry_points={
        'console_scripts': [
            'mcresolver = mcresolver.__main__:main'
        ]
    },
    install_requires=[
        'spiget==0.1.2',
        'tqdm==3.7.1',
        'cfscrape==1.4.3',
        'argparse',
        'pyBukGet==1.0.2',
        'PyYaml',
        'yamlbro==0.0.1',
        'requests',
        'Jinja2==2.8',
    ],
    setup_requires=[
        'pytest-runner'
    ],
    tests_require=[
        'pytest'
    ],
    dependency_links=[
        "https://github.com/TechnicalBro/pybukget/archive/1.0.2.zip#egg=pyBukGet-1.0.2",
        'https://github.com/TechnicalBro/yaml-bro/archive/0.0.1.zip#egg=yamlbro-0.0.1'
    ]
)
