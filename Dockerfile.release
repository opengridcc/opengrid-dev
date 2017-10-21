FROM opengrid/dev:latest

# install OpenGrid
RUN pip3 install opengrid

RUN cp -r /usr/local/lib/python3.5/dist-packages/opengrid/notebooks /root/notebooks

ADD ./opengrid/config/opengrid.cfg.example.docker /usr/local/lib/python3.5/dist-packages/opengrid/config/opengrid.cfg

WORKDIR /root/notebooks


