upgrade:
	cp ./catchall.py /usr/bin/catchall

install:
	mkdir -p /etc/catchall
	mkdir -p /etc/catchall/backup
	touch /etc/catchall/save.csv
	cp ./example_config /etc/catchall/config
	cp ./catchall.py /usr/bin/catchall
