from setuptools import setup, find_packages

setup(
    name="legal-knowledge-graph",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "legal-kg=legal_kg.main:main",
        ],
    },
)
