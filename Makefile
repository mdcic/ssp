name           = ssp
version       := $(shell sed -ne "0,/^v\([[:digit:].]\+\).*/ s//\1/p" ChangeLog)
spec           = ssp.spec
specin         = pkg/rpm/ssp.spec.in

#release: docs
#	python setup.py sdist register upload
.PHONY: docs srpm

docs:
	python setup.py build_sphinx

clean:
	rm -rf build dist docs/build
	rm -f MANIFEST *.log demos/*.log
	find ssp/ -name '*.pyc' -delete
	rm -f test.log ssp.spec
	rm -rf ssp.egg-info

spec:
	sed -e "/@DESCRIPTION@/ {r DESCRIPTION" -e "d;}" -e "s/@VERSION@/${version}/" ${specin} >${spec}

srpm: spec
	git archive -9 --format=tar.gz --prefix=${name}-${version}/ --output=${name}-${version}.tar.gz master
	rpmbuild -D '%_sourcedir ./' -D '%_srcrpmdir ./' --rmsource -bs ${spec}

test:
	python ./test.py
