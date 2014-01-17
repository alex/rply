from setuptools import setup


with open("README.rst") as f:
    readme = f.read()

setup(
    name="rply",
    description="A pure Python Lex/Yacc that works with RPython",
    long_description=readme,
    version="0.7.1",
    author="Alex Gaynor",
    author_email="alex.gaynor@gmail.com",
    packages=["rply"],
)
