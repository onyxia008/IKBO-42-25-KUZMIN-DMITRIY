#!/bin/bash
if [ -z "$1" ]; then
    echo "Использование: $0 <путь>"
    exit 1
fi

find "$1" -type f -exec md5sum {} + | sort | uniq -w32 -D
