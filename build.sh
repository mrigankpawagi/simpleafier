alias python=/usr/bin/python3.13

rm -r dist build *.egg-info
python -m build && python -m twine upload dist/*
