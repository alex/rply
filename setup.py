from setuptools import setup


with open("README.rst") as f:
    readme = f.read()

setup(
    name="rply",
    description="A pure Python Lex/Yacc that works with RPython",
    long_description=readme,
    # duplicated in docs/conf.py and rply/__init__.py
    version="0.7.6",
    author="Alex Gaynor",
    author_email="alex.gaynor@gmail.com",
    packages=["rply"],
    install_requires=["appdirs"],
)
