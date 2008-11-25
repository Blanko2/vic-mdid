pause You are about to delete your database, please cancel if this is not what you want!
mysqladmin -u root --force drop rooibos
mysqladmin -u root --default-character-set=utf8 create rooibos
python manage.py syncdb --noinput
python manage.py createcachetable cache
