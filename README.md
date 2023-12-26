# OpenVPN Manager

A Telegram bot that manages OpenVPN's profiles remotely in a Raspberry Pi.

## What's this for?

You just got a VPS, raspberry, whatever and you want to use it as a VPN (and
maybe other things too, not only as a VPN). You saw that OpenVPN let's you
create your own VPN server for free and is very compatible.

However, OpenVPN's interface for installing it and creating, managing and
revoking profiles (people that can use the VPN) is very counterintuitive. That's
why the community created `openvpn-install.sh`.

This script is very good but sometimes you'll need to edit the profiles while
you're not at home, and accessing the server console is not always possible.

This repository links the script's essentials to a Telegram Bot so new profiles
can be created, existing ones can be revoked, and only the whitelisted Telegram
users can do it!

# Try it!

Here are the steps that you will need to follow to install this project
in your Raspberry Pi (or other devices, but it hasn't been tested).

## Install OpenVPN

Download and run as administrator this script:

```sh
wget https://git.io/vpn -O openvpn-install.sh
sudo chmod +x openvpn-install.sh
sudo ./openvpn-install.sh
```

Follow the installator steps to install openvpn.
**You don't need to create any profile!** You can, if you want, but that's
what the Telegram bot will manage for you.

Remember that OpenVPN needs a static IP or a hostname (so you can use a
dynamic DNS if you don't have a static IP). Go to your router settings to
redirect the incoming port to your device, if you're behind a NAT. In this case,
it's also highly recomended to have a static LAN IP address.

## Install python prerequisites

```sh
sudo apt install python3 python3-pip
sudo python3 -m pip install telepot
```

## Running this program

Clone this repository

```sh
git clone https://github.com/royalmo/openvpn-manager.git
cd openvpn-manager
```

Now you need to edit the `settings.ini` file. There you will need to:

- **Get Telegram Bot Token:** Follow one of the thousand tutorials out there,
  or do it without tutorials (like pros do) talking to `@BotFather`.

- **Choose the name of the server:** Put a name for the server so people talking
  with the bot will know for which server they are talking to. For example you
  can use the device's hostname, location, city, model, ...

- **Set up admin UserIDs:** You will need to restart the telegram bot each time
  you modify these settings. Here you can put Key-Value pairs of name and
  Telegram userID of the users that can talk with the bot. Leave empty to
  accept any user (although this might be dangerous).

Once done, you can run this program:

```sh
sudo python3 main.py
```

## Run this program forever (even after restarts)

Add to `/etc/rc.local`, just before the `exit 0;` line:

```sh
python3 /home/pi/Documents/openvpn-manager/main.py
```
**Caution!** Be sure to change the path to wherever you cloned the repository.

Do you want to see the stdout of the program? You can use something like
GNU `screen`.

## Extra: customize the Telegram bot

By talkint to `@BotFather` you can make your bot a little bit more yours. One
of the cool features you can add is a list of available commands. This will
always be helpful to the users.

Here you have the screenshot of the commands I introduced in my bot:

<img width="370" alt="image" src="https://github.com/royalmo/openvpn-manager/assets/49844173/91f62329-eeb0-40f9-9a35-e911079d3831">

If you want to do it with your bot you will have to tell `/setcommands` to
`@BotFather`. Then, introduce the name of your bot. Once done, you can
write the command list, just like this example:

```
start - Welcome message.
help - Display the list of commands.
create - Create an OpenVPN profile.
revoke - Revoke an OpenVPN profile.
active - List active OpenVPN profiles.
```
