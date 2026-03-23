#!/bin/bash

# Define ANSI color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Neo4j
if curl -s -I http://localhost:7474 | grep -q "200 OK"; then
    echo -e "${GREEN}✅ Neo4j localhost:7474 UP${NC}"
else
    echo -e "${RED}❌ Neo4j localhost:7474 DOWN${NC}"
    exit 1
fi

echo -e "${GREEN}All checks passed.${NC}"
exit 0
