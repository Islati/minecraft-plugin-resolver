from setuptools import setup

setup(
    name='minecraftpluginresolver',
    version='0.1.0',
    packages=[
        'minecraftpluginresolver',
        'minecraftpluginresolver.scripts'
    ],
    url='',
    license='',
    author='Brandon Curtis',
    author_email='bcurtis@artectis.com',
    description="""
        Mimicking the structure of Requirements.txt,
        allows retrieval of Minecraft Server plugins in an easy, automated route.
        """,
    entry_points={
        'console_scripts': [
            'minecraftpluginresolver = minecraftpluginresolver.__main__:main'
        ]
    },
    install_requires=[
        'spiget==0.1.2',
        'tqdm==3.7.1',
        'cfscrape==1.4.3',
        'argparse==1.4.0',
        'pyBukGet==1.0.2',
        'PyYAML==3.11',
        'requests',
        'Jinja2==2.8'
    ],
    dependency_links=[
        "https://github.com/TechnicalBro/pybukget/archive/1.0.2.zip#egg=pyBukGet-1.0.2",
    ]
)