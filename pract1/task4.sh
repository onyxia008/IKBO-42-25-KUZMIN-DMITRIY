#!/bin/bash
grep -oE '[a-zA-Z_][a-zA-Z0-9_]*' "$1" | sort -u
