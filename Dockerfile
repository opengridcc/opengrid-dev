FROM ubuntu:14.04

RUN apt-get update
RUN apt-get -y install python-numpy python-scipy python-matplotlib python-pandas python-pip
RUN pip install -U pip ipython notebook
RUN pip install opengrid

VOLUME /usr/local/opengrid

WORKDIR /usr/local/opengrid/notebooks
CMD ipython notebook --ip='*'
