import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="oshi",
    version="0.0.1",
    author="sorashi",
    author_email="prazak.dennis@gmail.com",
    description="Japanese dictionary and grammar trainer",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sorashi/oshi",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=["lxml"]
)
