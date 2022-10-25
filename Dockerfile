# syntax=docker/dockerfile:1

FROM python:3.9.5

# install google chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get -y update
RUN apt-get install -y google-chrome-stable

# install chromedriver
RUN apt-get install -yqq unzip
RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip
RUN unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/

# INSTALL MSSQL ODBC DRIVERS
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN curl https://packages.microsoft.com/config/debian/9/prod.list > /etc/apt/sources.list.d/mssql-release.list
RUN apt-get -y update
RUN apt-get install -y --no-install-recommends \
        locales \
        apt-transport-https
RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen \
    && locale-gen 
RUN apt-get -y update
RUN apt-get install -y unixodbc-dev
RUN apt-get -y update
RUN ACCEPT_EULA=Y apt-get -y --no-install-recommends install msodbcsql17

RUN mkdir /code
WORKDIR /code

# copy separately to reuse cached dependencies so that when the code changes 
# dependencies won't be redownloaded (https://www.youtube.com/watch?v=zkMRWDQV4Tg&t=265s)
COPY ./requirements.txt /code   
RUN python -m pip install -U pip
RUN pip install --no-cache-dir --upgrade -r requirements.txt 

COPY . /code/

COPY . .

ENTRYPOINT [  ]
CMD ["python", "run_all.py