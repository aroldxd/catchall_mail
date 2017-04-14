install:
	mkdir -p /etc/catchall
	mkdir -p /etc/catchall/backup
	touch /etc/catchall/save.csv
#	cp ./example_config /etc/catchall/config
#	chmod +x ./catchall.py
	cp ./catchall.py /usr/bin/catchall
#	chmod 755 /etc/catchall/*
