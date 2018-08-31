import setuptools

setuptools.setup(
    name="g200s",
    version="0.0.2",
    author="Denis Ryabyy",
    author_email="vv1r0x@gmail.com",
    description="Python module for interacting with Ready For Sky Skykettle G200S Teapot",
    url="https://github.com/w1r0x/g200s",
    keywords=['r4s', 'g200s', 'skykettle', 'bluetooth'],
    packages=['g200s'],
    install_requires=[
        "bluepy",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
    ]
)
