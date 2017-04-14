# catchall_mail
This is a small util to enforce effective spam management for servers running postfix by creating a virtual address for every service and contact.
**This project is work in progress, pre alpha and [insert usual warnings]**

## how it works
Every contact gets an own email-address, consisting of a random prefix + an domainname (that you own and postfix is configured to listen on).
Emails that are send to those generated "virtual"-addresses are forwarded to your main email address.
The advantage of this is, that virtual addresses that get leaked to spam distributors can be easily renewed, the spam will not reach you anymore. Further, you can see **who** has leaked your address (and then take measures as renewing your password at that service).

## installation
* configure your main address in the config file
* 'make install' or create the directories and move the files yourself (see #files)
* make sure *catchall* always will have the necessary rights to access the files in /etc/catchall (e.g. 'chown -R [user] /etc/catchall')

## usage
catchall prints the usage if called without arguments

## config
| option | explanation |
|---|---|
| [main] | begin of config |
| domains | the mail domains you own and postfix ist configured on, comma seperated without spaces, first is default (see 'example_config') |
| mainaddr | the mail address incoming mail is redirected to |

## files
| file | function |
|------------------|---------------------|
| [basedir] | base directory, contains all files (defaults to /etc/catchall) |
| save.csv | contains virtual mailaddress to name relation |
| config | config file (take a look at 'default_config') |
| [basedir]/backup/ | contains backups of the savefile |
| /etc/postfix/virtual | file that tells postfix where to route virtual mail addresses |


## TODO
* improve installation (create and own directories) (makefile would do!)
