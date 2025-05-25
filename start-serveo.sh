#!/bin/sh

while true; do
  ssh -o StrictHostKeyChecking=no \
      -i /root/.ssh/id_rsa \
      -R radex-spark:80:api:8000 \
      serveo.net
  echo "Connection lost. Reconnecting in 5 seconds..."
  sleep 5
done