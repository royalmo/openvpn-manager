#!/bin/bash

case "$1" in
    enable)
        shift
        # Removing --now
        shift
        service="$1"
        shift
        echo "Enabled: $service"
        service "$service" start
        ;;
    disable)
        shift
        # Removing --now
        shift
        service="$1"
        shift
        echo "Disabled: $service"
        service "$service" stop
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
