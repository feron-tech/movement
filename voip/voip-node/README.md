## Build/Push Image

Use the corresponding scripts ```build.sh``` and ```push.sh```

## Run the container

docker run --rm -it  --name voip-node-cn -v ~/path/to/store/results:/monroe/results --privileged --net=host voip-node
