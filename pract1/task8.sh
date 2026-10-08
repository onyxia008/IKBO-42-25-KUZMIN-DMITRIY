#!/bin/bash
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Использование: $0 <каталог> <расширение>"
    exit 1
fi

find "$1" -type f -name "*.$2" -print0 | tar -czvf archive.tar.gz --null -T -
echo "Архив archive.tar.gz создан"
