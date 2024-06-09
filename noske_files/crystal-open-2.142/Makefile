SHELL=bash
export PATH := `pwd`/node-v16.16.0-linux-x64/bin/:$(PATH)
build: bundle.js
VERSION ?= `git describe --tags --always`
INSTALLDIR=/var/www/crystal

bundle.js:
	#wget https://nodejs.org/dist/v16.16.0/node-v16.16.0-linux-x64.tar.xz -O - | xz - -d| tar -x
	tar xf node-v16.16.0-linux-x64.tar.xz
	export PATH=$(PATH) && npm install --unsafe-perm=true
	export PATH=$(PATH) && node ./node_modules/.bin/webpack --config webpack.prod.js --output-filename bundle.js --output-path .

install: bundle.js
	mkdir -p $(DESTDIR)$(INSTALLDIR)
	# 1.js (WS visualization) is not a part of crystal-open
	cp viz.js vendors-viz.js 2.js $(DESTDIR)$(INSTALLDIR) || :
	cp -r bundle.js vendors-main.js app/{index.html,config.js,favicon.ico,images,libs,locale,styles,texts} $(DESTDIR)$(INSTALLDIR)
	sed -i "s/@VERSION@/$(VERSION)/" $(DESTDIR)$(INSTALLDIR)/index.html
	echo $(VERSION) > $(DESTDIR)$(INSTALLDIR)/version.txt
