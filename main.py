#!/bin/env/python3

import os
import sys
import time
import telepot
from io import StringIO
from configparser import ConfigParser
from telepot.loop import MessageLoop

# Thanks https://stackoverflow.com/q/1432924/9643618
os.chdir(os.path.dirname(os.path.abspath(__file__)))

config = ConfigParser()
config.read("settings.ini")

TOKEN = config["GENERAL"]["BOT_TOKEN"]
PERMITTED_CHATS = [int(x) for x in config["ADMINS"].values()]
SERVER_NAME = config["GENERAL"]["SERVER_NAME"]
VERBOSE_INFO = len(sys.argv) == 2 and sys.argv[1] == '-v'

def verbose(text):
    if not VERBOSE_INFO: return
    print(f"[INFO] {text}")

def get_active_profiles():
    """
    Returns a list of strings each representing an active OpenVPN profile.
    """
    verbose("Getting active profiles")
    stream = os.popen("tail -n +2 /etc/openvpn/server/easy-rsa/pki/index.txt | grep \"^V\" | cut -d '=' -f 2")
    active_profiles = list(filter(len, stream.read().split('\n')))
    verbose(f"Active profiles: {active_profiles}")
    return active_profiles


def create_profile(new_profile_name):
    """
    Creates an OpenVPN profile.

    Simulating SH (source: openvpn-install.sh):
    ```sh
    cd /etc/openvpn/server/easy-rsa/
    ./easyrsa --batch --days=3650 build-client-full "$client" nopass
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
    verbose(f"Started creating a profile: {new_profile_name}")
    os.chdir("/etc/openvpn/server/easy-rsa/")
    os.system(f"/etc/openvpn/server/easy-rsa/easyrsa --batch --days=3650 build-client-full {new_profile_name} nopass")
    output1 = os.popen("cat /etc/openvpn/server/client-common.txt").read()
    output2 = os.popen("cat /etc/openvpn/server/easy-rsa/pki/ca.crt").read()
    output3 = os.popen(f"sed -ne '/BEGIN CERTIFICATE/,$ p' /etc/openvpn/server/easy-rsa/pki/issued/{new_profile_name}.crt").read()
    output4 = os.popen(f"cat /etc/openvpn/server/easy-rsa/pki/private/{new_profile_name}.key").read()
    output5 = os.popen("sed -ne '/BEGIN OpenVPN Static key/,$ p' /etc/openvpn/server/tc.key").read()
    verbose("All commands executed, creating StringIO")

    return StringIO(f"{output1}<ca>\n{output2}</ca>\n<cert>\n{output3}</cert>\n<key>\n{output4}</key>\n<tls-crypt>\n{output5}</tls-crypt>\n")


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
    verbose(f"Starting commands to revoke a profile: {profile_name}")
    os.chdir("/etc/openvpn/server/easy-rsa/")
    os.system(f"/etc/openvpn/server/easy-rsa/easyrsa --batch revoke {profile_name}")
    os.system("/etc/openvpn/server/easy-rsa/easyrsa --batch --days=3650 gen-crl")
    os.system("rm -f /etc/openvpn/server/crl.pem")
    os.system("cp /etc/openvpn/server/easy-rsa/pki/crl.pem /etc/openvpn/server/crl.pem")
    os.system("chown nobody:nogroup /etc/openvpn/server/crl.pem")
    verbose("Profile revoked successfully")


def handle(msg):
    content_type, _, chat_id = telepot.glance(msg)
    print(f"[INFO] Got message from chat_id {chat_id}.")

    if content_type != 'text':
        return
    
    message = msg['text']
    print(f"[INFO] Message text: {message}")

    if message == '/start':
        bot.sendMessage(chat_id, f"Hello! I'm the manager of {SERVER_NAME}'s VPN services.\nType `/help` to see the available commands. Beware that you need to be an administrator in order to use me!", parse_mode='Markdown')
        return
    
    if message == '/help':
        bot.sendMessage(chat_id, "*BOT COMMANDS*\n`/start` - Welcome message.\n`/help` - Display the list of commands.\n`/create <profile_name>` - Create an OpenVPN profile.\n`/revoke <profile_name>` - Revoke an OpenVPN profile.\n`/active` - List active OpenVPN profiles.", parse_mode='Markdown')
        return

    if len(PERMITTED_CHATS) != 0 and chat_id not in PERMITTED_CHATS:
        verbose("User is not an ADMIN and whitelist is enabled. Aborting.")
        return
    
    if message.startswith('/create'):
        verbose("Processing /create command")
        splitted_message = message.split(' ')
        if len(splitted_message) != 2:
            bot.sendMessage(chat_id, "*SyntaxError!* Usage: `/create <new_profile_name>`", parse_mode='Markdown')
            verbose("Bad syntax. Aborting.")
            return
        new_profile_name = splitted_message[1]
        active_profiles = get_active_profiles()
        if new_profile_name in active_profiles:
            verbose("New profile name already in use. Aborting.")
            bot.sendMessage(chat_id, f"*ValueError!* Profile name `{new_profile_name}` is already in use!", parse_mode='Markdown')
            return
        bot.sendMessage(chat_id, f"*Done!* Profile name `{new_profile_name}` created!", parse_mode='Markdown')
        bot.sendDocument(chat_id, document=(f"{new_profile_name}.ovpn", create_profile(new_profile_name)))
        return

    if message.startswith('/revoke'):
        verbose("Processing /revoke command")
        splitted_message = message.split(' ')
        if len(splitted_message) != 2:
            bot.sendMessage(chat_id, "*SyntaxError!* Usage: `/revoke <profile_name>`", parse_mode='Markdown')
            verbose("Bad syntax. Aborting.")
            return
        profile_name = splitted_message[1]
        active_profiles = get_active_profiles()
        if profile_name not in active_profiles:
            bot.sendMessage(chat_id, f"*ValueError!* Profile name `{profile_name}` doesn't exist!", parse_mode='Markdown')
            verbose("Profile doesn't exist already. Aborting.")
            return
        revoke_profile(profile_name)
        bot.sendMessage(chat_id, f"*Done!* Profile name `{profile_name}` revoked!", parse_mode='Markdown')
        return

    if message.startswith('/active'):
        verbose("Processing /active command")
        active_profiles = get_active_profiles()
        if len(active_profiles) > 0:
            parsed_profiles = '\n- '.join(active_profiles)
            bot.sendMessage(chat_id, f"*ACTIVE OPENVPN PROFILES*\n- {parsed_profiles}", parse_mode='Markdown')
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
