To avoid crashing Chrome from within the container increase size of shared memory like so:

`docker run -it --shm-size=1g --rm parser`

To parse Artpole just run the image:

`docker run -it --shm-size=1g --rm parser`

To parse Petergof:

`docker run -it --shm-size=1g --rm parser python parse_petergof.py`


