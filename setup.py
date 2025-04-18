from setuptools import setup, find_packages

setup(
    name='Simpleafier',
    version='0.1.1',
    author='Mrigank Pawagi',
    author_email='mrigankpawagi@gmail.com',
    description='A command line tool to help improve the quality of Lean code by converting any "simp" to "simp only".',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/mrigankpawagi/Simpleafier',
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
    ],
    python_requires='>=3.6',
    install_requires=[
        dep.strip() for dep in open('requirements.txt').readlines()
    ],
    entry_points={
        'console_scripts': [
            'simpleafier=simpleafier.__init__:main',
        ],
    },
)
