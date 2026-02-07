import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs
import subprocess
import sys
import socket
import os
import tempfile
import re

ADDON = xbmcaddon.Addon()
ADDON_NAME = "Backlight"


def notify(message, icon=xbmcgui.NOTIFICATION_INFO):
    xbmcgui.Dialog().notification(ADDON_NAME, message, icon, 3000)


def get_settings():
    return {
        'tv_ip': ADDON.getSetting('tv_ip'),
        'ssh_user': ADDON.getSetting('ssh_user') or 'root',
        'ssh_key_path': ADDON.getSetting('ssh_key_path') or '/storage/.ssh/id_ed25519',
        'ssh_timeout': ADDON.getSetting('ssh_timeout') or '5'
    }


def piccap_command(settings, action):
    cmd = (
        'ssh -tt -o StrictHostKeyChecking=no -o ConnectTimeout={timeout} '
        '-i {key} {user}@{ip} '
        '"luna-send -n 1 \'luna://org.webosbrew.piccap.service/{action}\' \'{{}}\'"'
    ).format(
        timeout=settings['ssh_timeout'],
        key=settings['ssh_key_path'],
        user=settings['ssh_user'],
        ip=settings['tv_ip'],
        action=action
    )

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout


def discover_tvs():
    """Discover LG WebOS TVs on the network via SSDP."""
    ssdp_addr = '239.255.255.250'
    ssdp_port = 1900
    targets = [
        'urn:lge-com:service:webos-second-screen:1',
        'ssdp:all'
    ]

    tvs = {}

    for target in targets:
        msg = (
            'M-SEARCH * HTTP/1.1\r\n'
            'HOST: 239.255.255.250:1900\r\n'
            'MAN: "ssdp:discover"\r\n'
            'MX: 2\r\n'
            'ST: {}\r\n'
            '\r\n'
        ).format(target)

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(3)
            sock.sendto(msg.encode(), (ssdp_addr, ssdp_port))

            while True:
                try:
                    data, addr = sock.recvfrom(4096)
                    response = data.decode('utf-8', errors='ignore')
                    ip = addr[0]

                    if ip in tvs:
                        continue

                    # Look for LG indicators in the response
                    response_lower = response.lower()
                    if 'lge' in response_lower or 'lg' in response_lower or 'webos' in response_lower:
                        # Try to extract friendly name from LOCATION and fetch it
                        name = _get_tv_name(response, ip)
                        tvs[ip] = name
                except socket.timeout:
                    break
        except Exception:
            pass
        finally:
            try:
                sock.close()
            except Exception:
                pass

        if tvs:
            break

    return tvs


def _get_tv_name(ssdp_response, ip):
    """Try to extract TV name from SSDP LOCATION XML, fall back to IP."""
    location = None
    for line in ssdp_response.split('\r\n'):
        if line.lower().startswith('location:'):
            location = line.split(':', 1)[1].strip()
            break

    if not location:
        return 'LG TV ({})'.format(ip)

    try:
        # Fetch the device description XML
        import urllib.request
        req = urllib.request.Request(location, headers={'User-Agent': 'Kodi'})
        resp = urllib.request.urlopen(req, timeout=2)
        xml = resp.read().decode('utf-8', errors='ignore')
        # Extract <friendlyName>
        match = re.search(r'<friendlyName>(.*?)</friendlyName>', xml)
        if match:
            return match.group(1)
    except Exception:
        pass

    return 'LG TV ({})'.format(ip)


def ensure_ssh_key(key_path):
    """Generate an SSH key if one doesn't exist. Returns True on success."""
    if os.path.exists(key_path):
        return True

    key_dir = os.path.dirname(key_path)
    try:
        os.makedirs(key_dir, mode=0o700, exist_ok=True)
    except OSError:
        return False

    result = subprocess.run(
        ['ssh-keygen', '-t', 'ed25519', '-f', key_path, '-N', ''],
        capture_output=True, text=True
    )
    return result.returncode == 0


def copy_key_to_tv(settings, password):
    """Copy SSH public key to TV using password auth. Returns True on success."""
    pub_key_path = settings['ssh_key_path'] + '.pub'
    try:
        with open(pub_key_path, 'r') as f:
            pub_key = f.read().strip()
    except IOError:
        return False

    # Create a temporary askpass script
    askpass_fd, askpass_path = tempfile.mkstemp(prefix='piccap_askpass_', suffix='.sh')
    try:
        with os.fdopen(askpass_fd, 'w') as f:
            f.write('#!/bin/sh\necho "{}"\n'.format(password.replace('"', '\\"')))
        os.chmod(askpass_path, 0o700)

        remote_cmd = (
            "mkdir -p ~/.ssh && "
            "echo '{}' >> ~/.ssh/authorized_keys && "
            "chmod 700 ~/.ssh && "
            "chmod 600 ~/.ssh/authorized_keys"
        ).format(pub_key.replace("'", "'\\''"))

        cmd = (
            'ssh -o StrictHostKeyChecking=no -o ConnectTimeout={timeout} '
            '{user}@{ip} "{remote_cmd}"'
        ).format(
            timeout=settings['ssh_timeout'],
            user=settings['ssh_user'],
            ip=settings['tv_ip'],
            remote_cmd=remote_cmd.replace('"', '\\"')
        )

        env = os.environ.copy()
        env['SSH_ASKPASS'] = askpass_path
        env['SSH_ASKPASS_REQUIRE'] = 'force'
        env['DISPLAY'] = ':0'

        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            env=env, stdin=subprocess.DEVNULL
        )
        return result.returncode == 0
    finally:
        try:
            os.unlink(askpass_path)
        except OSError:
            pass


def test_ssh_connection(settings):
    """Test SSH connection to TV. Returns True if successful."""
    cmd = (
        'ssh -o StrictHostKeyChecking=no -o ConnectTimeout={timeout} '
        '-o BatchMode=yes -i {key} {user}@{ip} echo ok'
    ).format(
        timeout=settings['ssh_timeout'],
        key=settings['ssh_key_path'],
        user=settings['ssh_user'],
        ip=settings['tv_ip']
    )
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return 'ok' in result.stdout


def _offer_keymap_setup():
    """Offer to map the backlight toggle to a remote button."""
    dialog = xbmcgui.Dialog()

    if not dialog.yesno('Keymap Setup', 'Map the backlight toggle to a remote button?'):
        return

    buttons = ['Red', 'Green', 'Yellow', 'Blue', 'Subtitle', 'Audio']
    button_keys = ['red', 'green', 'yellow', 'blue', 'subtitle', 'audio']

    choice = dialog.select('Choose a button', buttons)
    if choice < 0:
        return

    button_name = buttons[choice]
    button_key = button_keys[choice]

    keymap_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<keymap>\n'
        '  <global>\n'
        '    <remote>\n'
        '      <{key}>RunScript(script.piccap)</{key}>\n'
        '    </remote>\n'
        '  </global>\n'
        '</keymap>\n'
    ).format(key=button_key)

    keymaps_dir = xbmcvfs.translatePath('special://userdata/keymaps/')
    if not os.path.exists(keymaps_dir):
        os.makedirs(keymaps_dir)

    keymap_path = os.path.join(keymaps_dir, 'piccap.xml')
    try:
        with open(keymap_path, 'w') as f:
            f.write(keymap_xml)
    except IOError:
        dialog.ok('Error', 'Failed to write keymap file.')
        return

    xbmc.executebuiltin('Action(reloadkeymaps)')
    notify('{} button mapped'.format(button_name))


def setup_wizard():
    """Guided setup wizard for first-time configuration."""
    dialog = xbmcgui.Dialog()
    settings = get_settings()

    # --- Step 1: TV Discovery ---
    notify("Scanning for LG TVs...")
    tvs = discover_tvs()

    if tvs:
        items = ['{} ({})'.format(name, ip) for ip, name in tvs.items()]
        items.append('Enter IP manually')
        ips = list(tvs.keys())

        choice = dialog.select('Select your LG TV', items)
        if choice < 0:
            return
        if choice < len(ips):
            tv_ip = ips[choice]
        else:
            tv_ip = dialog.input('Enter TV IP Address', type=xbmcgui.INPUT_IPADDRESS)
            if not tv_ip:
                return
    else:
        dialog.ok('TV Discovery', 'No LG TVs found on the network.\nYou can enter the IP address manually.')
        tv_ip = dialog.input('Enter TV IP Address', type=xbmcgui.INPUT_IPADDRESS)
        if not tv_ip:
            return

    settings['tv_ip'] = tv_ip

    # --- Step 2: SSH Key Check ---
    key_path = settings['ssh_key_path']
    if not os.path.exists(key_path):
        generate = dialog.yesno(
            'SSH Key',
            'No SSH key found at:\n{}\n\nGenerate a new key?'.format(key_path)
        )
        if generate:
            if ensure_ssh_key(key_path):
                notify("SSH key generated")
            else:
                dialog.ok('Error', 'Failed to generate SSH key.\nCheck the key path in settings.')
                return
        else:
            dialog.ok('SSH Key Required',
                       'An SSH key is needed to connect to the TV.\n'
                       'Set the key path in settings and re-run setup.')
            return

    # --- Step 3: Connection Test ---
    notify("Testing SSH connection...")
    if test_ssh_connection(settings):
        # Connection works, skip key copying
        ADDON.setSetting('tv_ip', tv_ip)
        _offer_keymap_setup()
        notify("Setup complete!", xbmcgui.NOTIFICATION_INFO)
        dialog.ok('Setup Complete',
                   'Connected to TV at {}\n\n'
                   'You can now use the backlight toggle.'.format(tv_ip))
        return

    # --- Step 4: Key Copying ---
    copy = dialog.yesno(
        'Copy SSH Key',
        'Could not connect with key authentication.\n\n'
        'Copy your SSH key to the TV?\n'
        'You will need the TV\'s root password.'
    )
    if not copy:
        dialog.ok('Setup Incomplete',
                   'Key-based SSH access is required.\n'
                   'Copy your key manually and re-run setup.')
        return

    password = dialog.input(
        'Enter TV root password',
        type=xbmcgui.INPUT_ALPHANUM,
        option=xbmcgui.ALPHANUM_HIDE_INPUT
    )
    if not password:
        return

    notify("Copying SSH key to TV...")
    if copy_key_to_tv(settings, password):
        notify("SSH key copied")
    else:
        dialog.ok('Error', 'Failed to copy SSH key to TV.\n'
                   'Check the password and try again.')
        return

    # Verify connection after key copy
    notify("Verifying connection...")
    if test_ssh_connection(settings):
        ADDON.setSetting('tv_ip', tv_ip)
        _offer_keymap_setup()
        notify("Setup complete!", xbmcgui.NOTIFICATION_INFO)
        dialog.ok('Setup Complete',
                   'Connected to TV at {}\n\n'
                   'You can now use the backlight toggle.'.format(tv_ip))
    else:
        dialog.ok('Setup Incomplete',
                   'Key was copied but connection test failed.\n'
                   'Check your settings and try again.')


def toggle():
    settings = get_settings()

    if not settings['tv_ip']:
        setup_wizard()
        return

    status = piccap_command(settings, "status")

    if '"isRunning":true' in status:
        piccap_command(settings, "stop")
        notify("Off")
    else:
        piccap_command(settings, "start")
        notify("On")


def start():
    settings = get_settings()

    if not settings['tv_ip']:
        setup_wizard()
        return

    piccap_command(settings, "start")
    notify("On")


def stop():
    settings = get_settings()

    if not settings['tv_ip']:
        setup_wizard()
        return

    piccap_command(settings, "stop")
    notify("Off")


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else None

    if action == "start":
        start()
    elif action == "stop":
        stop()
    elif action == "setup":
        setup_wizard()
    elif action == "settings":
        ADDON.openSettings()
    else:
        toggle()


if __name__ == '__main__':
    main()
