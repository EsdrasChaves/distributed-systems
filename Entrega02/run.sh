#!/bin/bash

python3 server.py localhost:2003 localhost:2002 localhost:2000 
python3 server.py localhost:2002 localhost:2001 localhost:2003 
python3 server.py localhost:2001 localhost:2000 localhost:2002 
python3 server.py localhost:2000 localhost:2003 localhost:2001 
