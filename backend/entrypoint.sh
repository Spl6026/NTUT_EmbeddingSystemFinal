#!/bin/bash
set -e

mkdir -p /root/.ssh
chmod 700 /root/.ssh

echo "Host *" > /root/.ssh/config
echo "StrictHostKeyChecking no" >> /root/.ssh/config
chmod 600 /root/.ssh/config

if [ -d "/ssh-host" ] && [ "$(ls -A /ssh-host)" ]; then
    echo "Copying SSH keys from host..."
    cp -r /ssh-host/* /root/.ssh/

    chmod 600 /root/.ssh/*
    chmod 600 /root/.ssh/config
else
    echo "No SSH keys found in /ssh-host volume."
fi

exec "$@"