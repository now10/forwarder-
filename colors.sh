#!/bin/bash
# Color definitions without tput

# Colors
BLACK='\033[0;30m'
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[0;37m'
RESET='\033[0m'

# Functions
print_green() {
    echo -e "${GREEN}$1${RESET}"
}

print_red() {
    echo -e "${RED}$1${RESET}"
}

print_blue() {
    echo -e "${BLUE}$1${RESET}"
}

print_yellow() {
    echo -e "${YELLOW}$1${RESET}"
}
