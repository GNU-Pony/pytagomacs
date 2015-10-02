# Copyright © 2013, 2014  Mattias Andrée (maandree@member.fsf.org)
# 
# Copying and distribution of this file, with or without modification,
# are permitted in any medium without royalty provided the copyright
# notice and this notice are preserved.  This file is offered as-is,
# without any warranty.
# 
# [GNU All Permissive License]


# The package path prefix, if you want to install to another root, set DESTDIR to that root
PREFIX = /usr
# The resource path excluding prefix
DATA = /share
# The library path excluding prefix
LIB = /lib
# The resource path including prefix
DATADIR = $(PREFIX)$(DATA)
# The library path including prefix
LIBDIR = $(PREFIX)$(LIB)
# The generic documentation path including prefix
DOCDIR = $(DATADIR)/doc
# The info manual documentation path including prefix
INFODIR = $(DATADIR)/info
# The license base path including prefix
LICENSEDIR = $(DATADIR)/licenses

# The name of the package as it should be installed
PKGNAME = pytagomacs
# The name of the module as it should be installed
MODULE = pytagomacs

# The major version number of the current Python installation
PY_MAJOR = $(shell python -V | cut -d ' ' -f 2 | cut -d . -f 1)
# The minor version number of the current Python installation
PY_MINOR = $(shell python -V | cut -d ' ' -f 2 | cut -d . -f 2)
# The version number of the current Python installation without a dot
PY_VER = $(PY_MAJOR)$(PY_MINOR)
# The version number of the current Python installation with a dot
PY_VERSION = $(PY_MAJOR).$(PY_MINOR)

# The modules this library is comprised of
SRC = common editor editring killring line

# Filename extension for -OO optimised python files
ifeq ($(shell test $(PY_VER) -ge 35 ; echo $$?),0)
PY_OPT2_EXT = opt-2.pyc
else
PY_OPT2_EXT = pyo
endif



.PHONY: all
all: compiled optimised

.PHONY: compiled
compiled: $(foreach M,$(SRC),src/__pycache__/$(M).cpython-$(PY_VER).pyc)

.PHONY: optimised
optimised: $(foreach M,$(SRC),src/__pycache__/$(M).cpython-$(PY_VER).$(PY_OPT2_EXT))


src/__pycache__/%.cpython-$(PY_VER).pyc: src/%.py
	python -m compileall $<

src/__pycache__/%.cpython-$(PY_VER).$(PY_OPT2_EXT): src/%.py
	python -OO -m compileall $<



.PHONY: install
install: install-base

.PHONY: install-all
install-all: install-base

.PHONY: install-base
install-base: install-lib install-copyright


.PHONY: install-lib
install-lib: install-source install-compiled install-optimised

.PHONY: install-source
install-source: $(foreach M,$(SRC),src/$(M).py)
	install -dm755 -- "$(DESTDIR)$(LIBDIR)/python$(PY_VERSION)/$(MODULE)"
	install -m644 $^ -- "$(DESTDIR)$(LIBDIR)/python$(PY_VERSION)/$(MODULE)"

.PHONY: install-compiled
install-compiled: $(foreach M,$(SRC),src/__pycache__/$(M).cpython-$(PY_VER).pyc)
	install -dm755 -- "$(DESTDIR)$(LIBDIR)/python$(PY_VERSION)/$(MODULE)/__pycache__"
	install -m644 $^ -- "$(DESTDIR)$(LIBDIR)/python$(PY_VERSION)/$(MODULE)/__pycache__"

.PHONY: install-optimised
install-optimised: $(foreach M,$(SRC),src/__pycache__/$(M).cpython-$(PY_VER).$(PY_OPT2_EXT))
	install -dm755 -- "$(DESTDIR)$(LIBDIR)/python$(PY_VERSION)/$(MODULE)/__pycache__"
	install -m644 $^ -- "$(DESTDIR)$(LIBDIR)/python$(PY_VERSION)/$(MODULE)/__pycache__"


.PHONY: install-copyright
install-copyright: install-copying install-license

.PHONY: install-copying
install-copying: COPYING
	install -dm755 -- "$(DESTDIR)$(LICENSEDIR)/$(PKGNAME)"
	install -m644 $^ -- "$(DESTDIR)$(LICENSEDIR)/$(PKGNAME)"

.PHONY: install-license
install-license: LICENSE
	install -dm755 -- "$(DESTDIR)$(LICENSEDIR)/$(PKGNAME)"
	install -m644 $^ -- "$(DESTDIR)$(LICENSEDIR)/$(PKGNAME)"



.PHONY: uninstall
uninstall:
	-rm -- "$(DESTDIR)$(LICENSEDIR)/$(PKGNAME)/LICENSE"
	-rm -- "$(DESTDIR)$(LICENSEDIR)/$(PKGNAME)/COPYING"
	-rmdir -- "$(DESTDIR)$(LICENSEDIR)/$(PKGNAME)"
	-rm -- $(foreach M,$(SRC),"$(DESTDIR)$(LIBDIR)/python$(PY_VERSION)/$(MODULE)/__pycache__/$(M).cpython-$(PY_VER).$(PY_OPT2_EXT)")
	-rm -- $(foreach M,$(SRC),"$(DESTDIR)$(LIBDIR)/python$(PY_VERSION)/$(MODULE)/__pycache__/$(M).cpython-$(PY_VER).pyc")
	-rm -- $(foreach M,$(SRC),"$(DESTDIR)$(LIBDIR)/python$(PY_VERSION)/$(MODULE)/$(M).py")
	-rmdir -- "$(DESTDIR)$(LIBDIR)/python$(PY_VERSION)/$(MODULE)/__pycache__/"
	-rmdir -- "$(DESTDIR)$(LIBDIR)/python$(PY_VERSION)/$(MODULE)"



.PHONY: clean
clean:
	-rm -r src/__pycache__

