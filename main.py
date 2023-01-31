#!/bin/env/python3

import os
import time
import telepot
from configparser import ConfigParser
from telepot.loop import MessageLoop

config = ConfigParser()
config.read("settings.ini")

OPENVPN_CONTROL_CHAT_ID = int(config["OPENVPN"]["CONTROL_CHAT_ID"])
TOKEN = config["TELEGRAM"]["BOT_TOKEN"]


def get_active_profiles():
    """
    Returns a list of strings each representing an active OpenVPN profile.
    """
    stream = os.popen("tail -n +2 /etc/openvpn/server/easy-rsa/pki/index.txt | grep \"^V\" | cut -d '=' -f 2")
    return stream.readlines()


def create_profile(new_profile_name):
    """
    Creates an OpenVPN profile.

    Simulating SH (source: openvpn-install.sh):
    ```sh
    {
    cat /etc/openvpn/server/client-common.txt
    echo "<ca>"
    cat /etc/openvpn/server/easy-rsa/pki/ca.crt
    echo "</ca>"
    echo "<cert>"
    sed -ne '/BEGIN CERTIFICATE/,$ p' /etc/openvpn/server/easy-rsa/pki/issued/"$client".crt
    echo "</cert>"
    echo "<key>"
    cat /etc/openvpn/server/easy-rsa/pki/private/"$client".key
    echo "</key>"
    echo "<tls-crypt>"
    sed -ne '/BEGIN OpenVPN Static key/,$ p' /etc/openvpn/server/tc.key
    echo "</tls-crypt>"
    } > ~/"$client".ovpn
    ```
    """
    output1 = os.popen("cat /etc/openvpn/server/client-common.txt").read()
    output2 = os.popen("cat /etc/openvpn/server/easy-rsa/pki/ca.crt").read()
    output3 = os.popen(f"sed -ne '/BEGIN CERTIFICATE/,$ p' /etc/openvpn/server/easy-rsa/pki/issued/{new_profile_name}.crt").read()
    output4 = os.popen(f"cat /etc/openvpn/server/easy-rsa/pki/private/{new_profile_name}.key").read()
    output5 = os.popen("sed -ne '/BEGIN OpenVPN Static key/,$ p' /etc/openvpn/server/tc.key").read()

    return f"{output1}<ca>{chr(10)}{output2}</ca>{chr(10)}<cert>{chr(10)}{output3}</cert>{chr(10)}<key>{chr(10)}{output4}</key>{chr(10)}<tls-crypt>{chr(10)}{output5}</tls-crypt>{chr(10)}"


def revoke_profile(profile_name):
    """
    Revokes an OpenVPN profile.

    Simulating SH (source: openvpn-install.sh):
    ```
    cd /etc/openvpn/server/easy-rsa/
    ./easyrsa --batch revoke "$client"
    ./easyrsa --batch --days=3650 gen-crl
    rm -f /etc/openvpn/server/crl.pem
    cp /etc/openvpn/server/easy-rsa/pki/crl.pem /etc/openvpn/server/crl.pem
    # CRL is read with each client connection, when OpenVPN is dropped to nobody
    chown nobody:nogroup /etc/openvpn/server/crl.pem
    ```
    """
    os.system(f"/etc/openvpn/server/easy-rsa/easyrsa --batch revoke {profile_name}")
    os.system("/etc/openvpn/server/easy-rsa/easyrsa --batch --days=3650 gen-crl")
    os.system("rm -f /etc/openvpn/server/crl.pem")
    os.system("cp /etc/openvpn/server/easy-rsa/pki/crl.pem /etc/openvpn/server/crl.pem")
    os.system("chown nobody:nogroup /etc/openvpn/server/crl.pem")


def handle(msg):
    content_type, _, chat_id = telepot.glance(msg)

    if (OPENVPN_CONTROL_CHAT_ID != 0 and chat_id != OPENVPN_CONTROL_CHAT_ID) or content_type != 'text':
        return
    
    message = msg['text']
    if message.startswith('/create'):
        splitted_message = message.split(' ')
        if len(splitted_message) != 2:
            bot.sendMessage(chat_id, "**SyntaxError!** Usage: `/create <new_profile_name>`", parse_mode='Markdown')
            return
        new_profile_name = splitted_message[1]
        active_profiles = get_active_profiles()
        if new_profile_name in active_profiles:
            bot.sendMessage(chat_id, f"**ValueError!** Profile name `{new_profile_name}` is already in use!", parse_mode='Markdown')
            return
        bot.sendMessage(chat_id, f"**Done!** Profile name `{new_profile_name}` created!", parse_mode='Markdown')
        bot.sendDocument(chat_id, document=create_profile(new_profile_name).encode("utf-8"), filename=f"{new_profile_name}.ovpn")
        return

    if message.startswith('/revoke'):
        splitted_message = message.split(' ')
        if len(splitted_message) != 2:
            bot.sendMessage(chat_id, "**SyntaxError!** Usage: `/revoke <profile_name>`", parse_mode='Markdown')
            return
        profile_name = splitted_message[1]
        active_profiles = get_active_profiles()
        if profile_name not in active_profiles:
            bot.sendMessage(chat_id, f"**ValueError!** Profile name `{new_profile_name}` doesn't exist!", parse_mode='Markdown')
            return
        revoke_profile(new_profile_name)
        bot.sendMessage(chat_id, f"**Done!** Profile name `{new_profile_name}` revoked!", parse_mode='Markdown')
        return

    if message.startswith('/active'):
        active_profiles = get_active_profiles()
        if len(active_profiles) > 0:
            parsed_profiles = '\n- '.join(active_profiles)
            bot.sendMessage(chat_id, f"**ACTIVE OPENVPN PROFILES**{chr(10)}- {parsed_profiles}", parse_mode='Markdown')
        else:
            bot.sendMessage(chat_id, "There aren't any active profiles to show.")
        return

    bot.sendMessage(chat_id, "Unknown command.")


bot = telepot.Bot(TOKEN)
MessageLoop(bot, handle).run_as_thread()

print('[INFO] OpenVPN Manager Telegram Bot Started successfully.')

# Keep the program running.
while 1:
    time.sleep(10)
