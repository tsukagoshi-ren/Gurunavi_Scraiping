from setuptools import setup, find_packages

setup(
    name="gurunavi-scraper",
    version="1.0.0",
    description="ぐるなび店舗情報スクレイピングツール",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.2",
        "pandas>=2.0.3",
        "openpyxl>=3.1.2",
        "lxml>=4.9.3",
    ],
    python_requires=">=3.8",
    entry_points={
        'console_scripts': [
            'gurunavi-scraper=gurunavi_scraper:main',
        ],
    },
)