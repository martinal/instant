#!/bin/sh

cd ../tests 
rm -rf ../build
sh clean.sh 
cd ../doc 
rm Instant-0.7.tar.gz
files=`find  ../../Instant-0.7 -type f| grep -v svn` 
echo $files 
tar -cf Instant-0.7.tar $files  
gzip Instant-0.7.tar
ls -s Instant-0.7.tar.gz
