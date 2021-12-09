from setuptools import find_packages, setup


setup(
    name = 'flask-blog',
    version = '1.0.0',
    author = 'Valtteri Rajalainen',
    description = 'Simple Flask blog webiste extended from the Flask tutorial app.',
    url = "https://github.com/varajala/templateman",
    python_requires = '>=3.7',
    packages = find_packages(),
)
