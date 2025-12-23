#!/bin/bash
set -e

mkdir -p /root/.ssh
cp -r /ssh-host/* /root/.ssh/

chmod 700 /root/.ssh
chmod 600 /root/.ssh/*

exec "$@"
