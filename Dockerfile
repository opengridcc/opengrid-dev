FROM ubuntu:14.04

RUN apt-get update
RUN apt-get -y install python-numpy python-scipy python-matplotlib python-pandas ipython ipython-notebook python-pip
RUN pip install gspread requests requests_futures

VOLUME /usr/local/opengrid

WORKDIR /usr/local/opengrid/opengrid/scripts
CMD ipython notebook --ip='*'
