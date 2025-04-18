rm -r dist build *.egg-info
python setup.py sdist bdist_wheel
python -m twine upload dist/*
