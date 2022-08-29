#!/bin/bash
sudo python3 northboundAPI.py &
sudo python3 southboundAPI.py &
sudo python3 db_daemon.py &