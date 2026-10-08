#!/bin/bash
text="$1"
len=${#text}
line="+"
for ((i=0; i<len+2; i++)); do line="${line}-"; done
line="${line}+"

echo "$line"
echo "| $text |"
echo "$line"
