VERSION = $(shell python -c 'from bodkin import __version__ as v; print(v, end="")')

dist: $(shell find src) LICENSE pyproject.toml README.md setup.cfg
	rm -f dist/*
	python3 -m build

install: dist
	python3 -m pip install --force-reinstall dist/bodkin-$(VERSION)-py3-none-any.whl
.PHONY: install

publish: test dist
	python3 -m twine upload dist/*
.PHONY: publish
.NOTPARALLEL: publish

test:
	pytest tests
.PHONY: test

format fmt:
	black .
.PHONY: format fmt

push: test
	git remote | xargs -n1 git push
	git remote | xargs -n1 git push --tags
.PHONY: push

tags: $(shell find bodkin -iname "*.py")
	ctags $^
.PHONY: tags
