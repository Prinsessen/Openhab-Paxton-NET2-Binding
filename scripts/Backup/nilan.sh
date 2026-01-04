#!/bin/sh

HOST='192.168.100.143'
USER='admin'
PASSWD='admin'
CMD='Reboot'

(
echo open "$HOST"
sleep 2
echo "$USER"
sleep 2
echo "$PASSWD"
sleep 2
echo "$CMD"
sleep 2
echo "exit"
) | telnet



