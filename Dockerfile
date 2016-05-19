FROM ubuntu:14.04

RUN apt-get update && apt-get -y install python-numpy python-scipy python-matplotlib python-pandas python-pip
RUN pip install -U pip jupyter

# download opengrid release and save the .tar.gz 
RUN pip download opengrid -d /home/root/temp/opengrid
RUN export OPENGRID_ARCHIVE=/home/root/temp/opengrid/$(ls /home/root/temp/opengrid/*.tar.gz)

# install opengrid
RUN pip install $OPENGRID_ARCHIVE

# create a working dir and copy notebooks
VOLUME /usr/local/opengrid
WORKDIR /usr/local/opengrid/notebooks
RUN tar xzf $OPENGRID_ARCHIVE -C /usr/local/opengrid --strip-components=1 ${OPENGRID_ARCHIVE%???????}/notebooks

CMD jupyter notebook --ip='*'
