#!/bin/bash

xterm -hold -e python3 server.py localhost:2008 localhost:2007 localhost:2000 &
xterm -hold -e python3 server.py localhost:2007 localhost:2006 localhost:2008 &
xterm -hold -e python3 server.py localhost:2006 localhost:2005 localhost:2007 &
xterm -hold -e python3 server.py localhost:2005 localhost:2004 localhost:2006 &
xterm -hold -e python3 server.py localhost:2004 localhost:2003 localhost:2005 &
xterm -hold -e python3 server.py localhost:2003 localhost:2002 localhost:2004 &
xterm -hold -e python3 server.py localhost:2002 localhost:2001 localhost:2003 &
xterm -hold -e python3 server.py localhost:2001 localhost:2000 localhost:2002 &
xterm -hold -e python3 server.py localhost:2000 localhost:2008 localhost:2001 &
