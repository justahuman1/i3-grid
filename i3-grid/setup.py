import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="i3-grid-justahuman1",
    version="0.2.2",
    author="Sai Valla",
    author_email="justahuman1@github.com",
    description="A floating window management extension for i3.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/justahuman1/i3-grid",
    packages=setuptools.find_packages(),
    install_requires=[
        'i3-py',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU GPL 3 License",
        "Operating System :: Linux",
    ],
    python_requires='>=3.6',
)
