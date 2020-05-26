import setuptools

try:
    with open("README.md", "r") as fh:
        long_description = fh.read()
except:
    long_description = "An i3wm extension for taming floating windows in ~65kB."

setuptools.setup(
    name="i3-grid",
    version="0.2.3b1",
    author="Sai Valla",
    author_email="justahuman1@github.com",
    description="A floating window extension for i3.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/justahuman1/i3-grid",
    packages=setuptools.find_packages(),
    install_requires=["i3-py"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.6",
)
