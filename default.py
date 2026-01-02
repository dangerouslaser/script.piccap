import xbmc
import xbmcaddon
import xbmcgui
import subprocess
import sys

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


def toggle():
    settings = get_settings()
    
    if not settings['tv_ip']:
        notify("Please configure TV IP in settings", xbmcgui.NOTIFICATION_WARNING)
        ADDON.openSettings()
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
        notify("Please configure TV IP in settings", xbmcgui.NOTIFICATION_WARNING)
        ADDON.openSettings()
        return
    
    piccap_command(settings, "start")
    notify("On")


def stop():
    settings = get_settings()
    
    if not settings['tv_ip']:
        notify("Please configure TV IP in settings", xbmcgui.NOTIFICATION_WARNING)
        ADDON.openSettings()
        return
    
    piccap_command(settings, "stop")
    notify("Off")


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else None
    
    if action == "start":
        start()
    elif action == "stop":
        stop()
    elif action == "settings":
        ADDON.openSettings()
    else:
        toggle()


if __name__ == '__main__':
    main()
