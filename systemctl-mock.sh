#!/bin/bash

case "$1" in
    enable)
        shift
        service="$1"
        shift
        echo "Enabled: $service"
        service "$service" start
        ;;
    disable)
        shift
        service="$1"
        shift
        echo "Disabled: $service"
        # This is a no-op
        ;;
    is-active)
        shift
        service="$1"
        shift
        echo "Active: $service"
        # Always return false
        exit 1
        ;;
    *)
        echo "Usage: $0 {enable|disable|is-active} [service]"
        exit 1
        ;;
esac
