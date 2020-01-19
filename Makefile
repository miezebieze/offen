.PHONY: clean push

play: vbuild
	. venv/bin/activate; python -m offen.example

vbuild: venv
	. venv/bin/activate; python setup.py sdist bdist_wheel

push:
	git commit -a
	git fetch
	git rebase
	git push

venv: venv/bin/activate
venv/bin/activate: requirements.txt
	test -d venv || virtualenv venv
	. venv/bin/activate; pip install -Ur requirements.txt
	touch venv/bin/activate

