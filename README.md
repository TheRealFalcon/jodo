# JODO

Jodo provides a single CLI interface to interact with multiple cloud providers.

## Installation

While it can be `pip install`ed into any environment, [pipx](https://pypa.github.io/pipx/) is recommended:

```bash
pipx install jodo
```

## Usage

### Launch an LXD container

```bash
jodo launch --cloud lxd_container --image jammy my-instance
```

### List all instances

```bash
$ jodo list
NAME         CLOUD          IP              CREATED
my-instance  lxd_container  10.197.203.205  2023-10-18 01:33:16
```

### SSH into instance

```bash
jodo ssh my-instance
Warning: Permanently added '10.197.203.205' (ED25519) to the list of known hosts.
Welcome to Ubuntu 22.04.3 LTS (GNU/Linux 6.5.0-7-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

  System information as of Wed Oct 18 01:33:15 UTC 2023

  System load:           0.86572265625
  Usage of /home:        unknown
  Memory usage:          0%
  Swap usage:            0%
  Temperature:           47.0 C
  Processes:             27
  Users logged in:       0
  IPv4 address for eth0: 10.197.203.205
  IPv6 address for eth0: fd42:eaab:10a1:ad48:216:3eff:fef2:9ded


Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


The list of available updates is more than a week old.
To check for new updates run: sudo apt update

To run a command as administrator (user "root"), use "sudo <command>".
See "man sudo_root" for details.

ubuntu@my-instance-0:~$
```

### Delete instance

```bash
jodo delete my-instance
```

## Status

This is a project I quickly hacked together in my free time and should be considered minimum viable functionality. It currently has no testing, no logging, no exception handling, no documentation (other than this README), and no guantees about state or schema compatibility. If you use it you will see glaringly obvious bugs. Feel free to submit an issue or PR.
