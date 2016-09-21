#
# Build an image for deploying the Neuromorphic benchmarks server
#
# To build the image:
#   docker build -t cnrsunic/neuromorphic_benchmarks_service .
#
# To run the application:
#  docker run -d -p 443 cnrsunic/neuromorphic_benchmarks_service
#
# To find out which port to access on the host machine, run "docker ps"
#

FROM debian:jessie
MAINTAINER Andrew Davison <andrew.davison@unic.cnrs-gif.fr>

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update --fix-missing
RUN apt-get -y -q install nginx-extras supervisor build-essential python-dev python-setuptools python-pip sqlite3 python-psycopg2
RUN unset DEBIAN_FRONTEND

RUN pip install uwsgi

ADD . /home/docker/site

RUN pip install -r /home/docker/site/deployment/requirements.txt

WORKDIR /home/docker/site
ENV PYTHONPATH  /home/docker:/usr/local/lib/python2.7/dist-packages

RUN python manage.py check
#RUN python manage.py migrate
#RUN python manage.py loaddata benchmarks_site/initial_data.json
#RUN python manage.py collectstatic --noinput
RUN unset PYTHONPATH

RUN echo "daemon off;" >> /etc/nginx/nginx.conf
RUN rm /etc/nginx/sites-enabled/default
RUN ln -s /home/docker/site/deployment/nginx-app.conf /etc/nginx/sites-enabled/
RUN ln -s /home/docker/site/deployment/supervisor-app.conf /etc/supervisor/conf.d/
RUN ln -sf /dev/stdout /var/log/nginx/access.log
RUN ln -sf /dev/stderr /var/log/nginx/error.log

ENV PYTHONPATH /usr/local/lib/python2.7/dist-packages:/usr/lib/python2.7/dist-packages
EXPOSE 443
CMD ["supervisord", "-n", "-c", "/etc/supervisor/conf.d/supervisor-app.conf"]
