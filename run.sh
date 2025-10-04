#!/bin/bash
# SHYpn - Run script with system Python and GTK3
#
# NOTE: This script uses SYSTEM PYTHON (/usr/bin/python3) instead of conda
# because conda's pygobject package has broken Cairo integration
# ("Couldn't find foreign struct converter for 'cairo.Context'")

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Starting SHYpn with system Python...${NC}"

# Use system Python which has proper PyGObject + Cairo integration
/usr/bin/python3 src/shypn.py
