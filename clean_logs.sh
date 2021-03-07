#!/bin/sh
for dir in server client
do
    echo "Removing logs in $dir directory..."
    rm -r -f $dir/logs/*
done