from distutils.core import setup

from pip.req import parse_requirements


def main():
    setup(
        name='spigotresolver',
        version='0.0.1',
        packages=[
            'spigotresolver'
        ],
        url='',
        license='',
        author='Brandon Curtis',
        author_email='bcurtis@artectis.com',
        description='Mimicking the structure of Requirements.txt, allows retrieval of Spigot.org plugins in an easy, automated route.',
        install_requires=reqs
    )


if __name__ == "__main__":
    reqs = parse_requirements('requirements.txt', session=False)
    reqs = [ir for ir in reqs]

    main()
