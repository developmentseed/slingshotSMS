buildmac:
	python setup.py py2app --iconfile=app_icon.icns
	echo "Removing Frameworks"
	cp -r web dist/SlingshotSMS.app/Contents/MacOS
	unzip -n dist/SlingshotSMS.app/Contents/Resources/lib/python2.6/site-packages.zip -d dist/SlingshotSMS.app/Contents/Resources/lib/python2.6/
	rm -r dist/SlingshotSMS.app/Contents/Frameworks/{GEOS.Framework,PROJ.Framework,libpq.5.dylib}