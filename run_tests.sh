#!/bin/bash

echo -n "Test database.py... "
python3 src/database.py
if [ $? -eq 0 ]; then echo "ok"; else exit 1; fi

