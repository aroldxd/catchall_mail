# catchall_mail
This is a small util to enforce effective spam management for servers running postfix.

## how it works
Every contact gets an own email-address, consisting of a random prefix + an domainname (that you own and postfix is configured to listen on).
Emails that are send to those generated "virtual"-addresses are forwarded to your main email address.
The advantage of this is, that virtual addresses that get leaked to spam distributors can be easily renewed, the spam will not reach you anymore. Further, you can see **who** has leaked your address (and then take measures as renewing your password at that service).

## installation
* configure your main address in the config file
* first run has to be done with the necessary rights to create directories in /etc
* make sure *catchall* always will have the necessary rights to access the files in /etc/catchall (e.g. 'chown -R [user] /etc/catchall')
* you can move the executable ('catchall.py') to /usr/bin/catchall, then you can use the catchall command directly in your shell / crontab / whatever
