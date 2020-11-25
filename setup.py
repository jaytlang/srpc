import setuptools

with open("README.md") as f:
    long_description = f.read()

setuptools.setup(
    name="sRPC",
    version="1.0.0",
    author="Ravi Rahman",
    author_email="r_rahman@mit.edu",
    description="sRPC",
    long_description=long_description,
    url="https://github.com/jaytlang/srpc",
    packages=setuptools.find_packages(),
    install_requires=[
    ],
    entry_points = {
        "console_scripts": [
            'srpc-connect=srpc.client.connect:connect'
        ]
    },
    include_package_data=True,
    scripts=[
    ]
)