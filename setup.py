from setuptools import setup, find_packages

setup(
    name="bulk-id3-tagger",
    version="0.1.0",
    description="Generate a JSON tagging template from a folder of audio files, then bulk-write ID3 tags and artwork from that JSON.",
    packages=find_packages(),
    install_requires=[
        "mutagen>=1.47",
    ],
    entry_points={
        "console_scripts": [
            "bulk-id3-tagger=bulk_id3_tagger.__main__:main",
        ],
    },
    python_requires=">=3.8",
)
