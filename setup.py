from setuptools import setup

setup(
    name='SSAPI',
    packages=['SSAPI'],
    include_package_data=True,
    install_requires=[
        'flask',
        'flask-restplus',
        'flask-jwt',
        'flask-sqlalchemy',
    ],
)
