FROM rappdw/docker-java-python:openjdk1.8.0_171-python3.6.6
RUN java -version
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
RUN pip install --upgrade pip
RUN pip3 install requests
RUN pip install discord.py
RUN pip install matplotlib
ADD requirements.txt /code/
RUN pip install -r requirements.txt
RUN pip install django-multiforloop
ADD . /code/
