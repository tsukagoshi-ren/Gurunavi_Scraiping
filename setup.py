from setuptools import setup, find_packages

setup(
    name="gurunavi-scraper-pro",
    version="2.0.0",
    description="ぐるなび店舗情報スクレイピングツール Professional Edition",
    author="Developer",
    author_email="developer@example.com",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.2",
        "pandas>=2.0.3",
        "openpyxl>=3.1.2",
        "lxml>=4.9.3",
        "selenium>=4.15.0",
        "webdriver-manager>=4.0.1",
    ],
    python_requires=">=3.8",
    entry_points={
        'console_scripts': [
            'gurunavi-scraper=production_ready_scraper:main',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)