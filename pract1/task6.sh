#!/bin/bash
dir="${1:-.}"   # если аргумент не указан, берём текущую папку

shopt -s nullglob

for file in "$dir"/*.{c,js,py}; do
    first_line=$(head -n 1 "$file")

    # Комментарии: // или /* (C, C++, JS) и # (Python)
    if [[ "$first_line" =~ ^[[:space:]]*(//|/\*|#) ]]; then
        echo "$file: комментарий есть"
    else
        echo "$file: комментария нет"
    fi
done
