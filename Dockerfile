# Dockerfile maintained by Eric Roy <eric@ericroy.net>.

# WARNING: This image won't work right away. After building and running
# the image you need to install openvpn on the container itself.
# This is done so secret keys are generated differently for each container.

# Build the container: docker build -t openvpn-manager .
# Run the container: docker run -d openvpn-manager
# Install OpenVPN: docker exec -it openvpn-manager /openvpn-install.sh
# Test then the Telegram bot, not before!

FROM debian:stable

# Install dependencies
RUN apt update
RUN apt install -y python3 python3-telepot

# Install openvpn
RUN wget https://git.io/vpn -O openvpn-install.sh
RUN chmod +x  openvpn-install.sh

# Copy telegram bot
RUN mkdir openvpn-bot
COPY main.py /openvpn-bot/

# Expose the VPN port (1194 is the default one but choose what you want)
EXPOSE 1194

# Start command
CMD python3 openvpn-bot/main.py
