To build an image from the `app` folder:  
`docker build -t sashakang/parser .`

To avoid crashing Chrome from within the container increase size of shared memory like so:  
`docker run -it --shm-size=1g --rm sashakang/parser`

To parse Artpole just run the image:  
`docker run -it --shm-size=1g --rm sashakang/parser`

To parse Petergof:  
`docker run -it --shm-size=1g --rm sashakang/parser python parse_petergof.py`

To schedule a job need root privileges for cron:  
`sudo crontab -eu root`

To run container in cron do not use `-it` option, i.e.  
`docker run --shm-size=1g --rm parser python parse_petergof.py`

To keep credentials use volume mount. Do not use bind mount as its path can be modified and thus the code can get access to any data.

To create volume:  
`sudo docker volume create uduntu-dsk`

The local folder containing the data is:  
`/var/lib/docker/volums/[disk name]/_data/`

To bind volume:  
`sudo docker run -v uduntu-dsk:/path/to/folder [image_name]`

Started from the `parsing` folder on Windows  
`docker run -it -v "$(pwd):/code" --rm sashakang/parser`  
Mounts `parsing` folder as /code. But the path to access the credentials will be different for Linux. Still need to work on it.

Docker volume data location (type in file browser):  
`\\wsl$\docker-desktop-data\version-pack-data\community\docker\volumes\parser-vol\_data\`

To run container on Windows or Linux:  
`docker run -it -v parser-vol:/credentials --rm --shm-size=1g sashakang/parser`  
provided `.server_analytics` file located in the root of the volume.