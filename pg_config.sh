apt-get -qqy update
apt-get -qqy install postgresql python-psycopg2
apt-get -qqy install python-flask python-sqlalchemy
apt-get -qqy install python-pip
pip install werkzeug==0.8.3
pip install flask==0.9
pip install Flask-Login==0.1.3
pip install oauth2client
pip install requests
pip install httplib2
pip install bleach
pip install redis
pip install passlib
pip install itsdangerous
pip install flask-httpauth

su postgres -c 'createuser -dRS vagrant'
su vagrant -c 'createdb'
vagrantTip="[35m[1mThe shared directory is located at /vagrant\nTo access your shared files: cd /vagrant(B[m"
echo -e $vagrantTip > /etc/motd