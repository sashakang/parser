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


# RUN apt -y install curl
# RUN apt -y install gnupg2
# # INSTALL MSSQL ODBC DRIVERS
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN curl https://packages.microsoft.com/config/debian/9/prod.list > /etc/apt/sources.list.d/mssql-release.list
RUN apt-get install -y --no-install-recommends \
        locales \
        apt-transport-https
RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen \
    && locale-gen 
RUN apt-get -y update
RUN apt-get install -y unixodbc-dev
RUN apt-get -y update
RUN ACCEPT_EULA=Y apt-get -y --no-install-recommends install msodbcsql17

# install pyodbc separately
# RUN apt-get update && apt-get install -y \
#     --no-install-recommends \
#     unixodbc-dev \
#     unixodbc \
#     libpq-dev 

# COPY requirements.txt requirements.txt

# set display port to avoid crash
# ENV DISPLAY=:99

RUN mkdir /code
WORKDIR /code

COPY . /code/

RUN python -m pip install -U pip
RUN pip install -r requirements.txt 
COPY . .

ENTRYPOINT [  ]
CMD ["python", "parse_artpole.py"]