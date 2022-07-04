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

# build from `app` folder
WORKDIR /SynologyDrive/dikart/parsing/app/
# WORKDIR .

# RUN apt -y install curl
# RUN apt -y install gnupg2
# # INSTALL MSSQL ODBC DRIVERS
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list
RUN apt-get -y update
# RUN ACCEPT_EULA=Y apt-get install -y mssql-tools18
RUN ACCEPT_EULA=Y apt-get -y install msodbcsql17

# # optional: for bcp and sqlcmd
# RUN ACCEPT_EULA=Y apt-get install -y mssql-tools18
# echo 'export PATH="$PATH:/opt/mssql-tools18/bin"' >> ~/.bashrc
# source ~/.bashrc
# optional: for unixODBC development headers
RUN apt-get install -y unixodbc-dev


# install pyodbc separately
# RUN apt-get update && apt-get install -y \
#     --no-install-recommends \
#     unixodbc-dev \
#     unixodbc \
#     libpq-dev 

# COPY requirements.txt requirements.txt

# set display port to avoid crash
ENV DISPLAY=:99

RUN mkdir /code
WORKDIR /code

COPY . /code/


RUN python -m pip install -U pip


RUN pip install -r requirements.txt 
# --no-index --find-links file://SynologyDrive/dikart/parsing/app/venv/Lib/site-packages/

COPY . .

# CMD ["sh"]
CMD ["python", "parse_artpole.py"]
# CMD ["python", "parse_petergof.py"]