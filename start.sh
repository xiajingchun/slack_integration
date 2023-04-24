#!/bin/bash

nohup /usr/local/python3/bin/gunicorn -w 2 -b 0.0.0.0:5000 postman:app > postman.log 2>&1 &


