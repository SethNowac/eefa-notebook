#!/usr/bin/bash

# Check that this script is in the correct folder
if [ $(basename "$(pwd)") != "book" ]; then
    echo "This script must be inside the 'book' directory of the eefa-notebook repository! Exiting..."
    exit 1
fi

# Register user input
if [ $# -lt 1 ] || [ $# -gt 1 ]; then
    echo "Only one argument should be supplied. (Usage: sh refined_file_organizer.sh [dir_name]). Exiting..."
    exit 1
fi

# First, check if provided directory exists
if [ ! -d "$1" ]; then
    echo "Directory '$1' does not exist. (Usage: sh refined_file_organizer.sh [dir_name]). Exiting..."
    exit 1
fi
refined_directory=$1

# Add action warning so the user doesn't accidentally make a critical mistake
read -r -p "Proceed with directory $(basename "$refined_directory")? [y/N]: " response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]
then
    # Sort the files in each folder into their own directories
    find . -type f -name "*sort_checkpoint_files.sh" -execdir sh {} \;

    ./refined_script_sorter.sh "$refined_directory"
else
    echo "Exiting..."
fi