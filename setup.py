from pip._internal.download import PipSession
from pip._internal.req import parse_requirements
from setuptools import setup, find_packages

from application import __version__ as version

requirements = [
    str(req.req) for req in parse_requirements('requirements.txt', session=PipSession())
]

setup(
    name="influential_users",
    version=version,
    author="Alexandru Grigoras",
    author_email="alex_grigoras_10@yahoo.com",
    description="Determining the most influential users from the multimedia social network YouTube by creating a graph with the most important users / channels.",
    url="https://github.com/alexgrigoras/influential_users",
    packages=find_packages(),
    keywords='youtube search influential users',
    install_requires=requirements,
    zip_safe=True,
    classifiers=[
        'Development Status :: 1.0 - Development',
        "Programming Language :: Python :: 3.7",
        "Crawler :: Youtube metadata crawler",
        "Operating System :: OS Independent",
    ]
)
