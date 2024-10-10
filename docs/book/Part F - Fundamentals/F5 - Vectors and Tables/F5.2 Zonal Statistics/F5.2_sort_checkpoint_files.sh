#!/usr/bin/bash

# Variables
list_unused_auto_converted_files=(
'F52a Checkpoint_geemap' 
'F52b Checkpoint_geemap'
)

js_file_name='./1.javascript'
auto_converted_file_name='./2.auto-converted'
refined_file_name='./3.refined-working'

# Prep stage: if js directory already exists, move everything out of it
if [ -d $js_file_name ]; then
    mv $js_file_name/* .
fi

# Cleanup stage 1: remove duplicate checkpoints
find . -type f -not -name '*_geemap.ipynb' -name '*.ipynb' -exec rm -f {} +
find . -type f -not -name '*_geemap.py' -name '*.py' -exec rm -f {} +

# Cleanup stage 2: move JS files into special folder
mkdir $js_file_name
mv *.js $js_file_name

# Cleanup stage 3: move auto-converted files into 2.auto-converted and delete unused auto-converted files
for ((i = 0; i < ${#list_unused_auto_converted_files[@]}; i++))
do
    rm "${list_unused_auto_converted_files[$i]}".py
    rm "${list_unused_auto_converted_files[$i]}".ipynb
done


mkdir $auto_converted_file_name
mv *_geemap.ipynb $auto_converted_file_name
mv *_geemap.py $auto_converted_file_name

# Cleanup stage 4. create space for anything that needs refined in order to work
mkdir $refined_file_name