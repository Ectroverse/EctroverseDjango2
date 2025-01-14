FROM python:3.11
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
RUN pip install --upgrade pip
RUN pip3 install requests
RUN pip install discord.py
ADD requirements.txt /code/
RUN pip install -r requirements.txt
RUN pip install django-multiforloop
RUN pip install django-utils-six
ADD . /code/