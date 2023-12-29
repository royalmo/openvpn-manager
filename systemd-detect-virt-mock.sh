#!/bin/bash

if [ "$1" = "-cq" ]; then
  exit 1
else
  echo "kvm"
  exit 0
fi
