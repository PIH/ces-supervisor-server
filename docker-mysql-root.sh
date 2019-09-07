#!/bin/bash

docker exec -it $(docker ps | grep openmrs-sdk-mysql | cut -f1 -d' ') mysql -u root -p
