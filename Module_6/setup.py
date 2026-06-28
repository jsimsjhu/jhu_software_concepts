from setuptools import setup, find_packages

setup(
    name="gradcafe_analysis",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "flask>=3.0",
        "psycopg[binary]>=3.2",
        "beautifulsoup4>=4.12",
        "selenium>=4.15",
        "requests>=2.31",
    ],
    python_requires=">=3.10",
)