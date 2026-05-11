from setuptools import setup, find_packages

setup(
    name="social-media-automation",
    version="1.0.0",
    description="Schedule and publish AI-generated posts to Twitter and LinkedIn",
    python_requires=">=3.11",
    packages=find_packages(),
    install_requires=[
        "anthropic>=0.40.0",
        "requests>=2.31.0",
        "requests-oauthlib>=1.3.1",
        "click>=8.1.7",
        "tabulate>=0.9.0",
    ],
    entry_points={
        "console_scripts": [
            "sma=social_media_automation.cli.commands:cli",
        ],
    },
)
