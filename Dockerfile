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

FROM debian:buster-slim
MAINTAINER Andrew Davison <andrew.davison@cnrs.fr>

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update --fix-missing
RUN apt-get -y -q install nginx-extras supervisor build-essential python3-dev python3-setuptools python3-pip sqlite3 python3-psycopg2
RUN unset DEBIAN_FRONTEND

RUN pip3 install uwsgi

ADD . /home/docker/site

RUN pip3 install -r /home/docker/site/deployment/requirements.txt

WORKDIR /home/docker/site
ENV PYTHONPATH  /home/docker:/usr/local/lib/python3.7/dist-packages

RUN python3 manage.py check
#RUN python3 manage.py collectstatic --noinput
RUN unset PYTHONPATH

RUN echo "daemon off;" >> /etc/nginx/nginx.conf
RUN rm /etc/nginx/sites-enabled/default
RUN ln -s /home/docker/site/deployment/nginx-app.conf /etc/nginx/sites-enabled/
RUN ln -s /home/docker/site/deployment/supervisor-app.conf /etc/supervisor/conf.d/
RUN ln -sf /dev/stdout /var/log/nginx/access.log
RUN ln -sf /dev/stderr /var/log/nginx/error.log

ENV PYTHONPATH /usr/local/lib/python3.7/dist-packages:/usr/lib/python3.7/dist-packages
EXPOSE 443
CMD ["supervisord", "-n", "-c", "/etc/supervisor/conf.d/supervisor-app.conf"]
