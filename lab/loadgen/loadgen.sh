#!/bin/sh
# Steady synthetic traffic so faults produce observable symptoms in logs.
sleep 3
while true; do
    curl -s -o /dev/null -m 15 \
        -w "GET /orders %{http_code} %{time_total}s\n" http://nginx/orders
    sleep 1
    curl -s -o /dev/null -m 15 -X POST \
        -w "POST /jobs %{http_code} %{time_total}s\n" http://nginx/jobs
    sleep 2
done
