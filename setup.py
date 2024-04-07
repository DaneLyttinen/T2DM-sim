from setuptools import setup

setup(
    name="T2DMSimulator",
    version="0.0.1",
    description="A Type-2 Diabetes Simulator as a Reinforcement Learning Environment in OpenAI gym or rllab",
    url="https://github.com/DaneLyttinen/T2DM-sim",
    author="Dane Lyttinen",
    author_email="dane2000@live.se",
    license="MIT",
    packages=["T2DMSimulator"],
    install_requires=[
        "gymnasium~=0.29.1",
        "pathos>=0.3.1",
        "scipy>=1.7.0",
        "matplotlib>=3.7.2",
        "numpy>=1.20.3",
        "pandas>=2.0.3",
    ],
    include_package_data=True,
    zip_safe=False,
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
)