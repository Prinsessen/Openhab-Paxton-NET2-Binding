#!/bin/bash

_now=$(date +"%m_%d_%Y_%H%M%S")

sudo /usr/share/openhab/runtime/bin/backup /mnt/OH5Backup/"OH5backup_$_now"
