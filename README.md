# Piccap Backlight Toggle for Kodi

Toggle the Piccap screen capture service on rooted LG WebOS TVs for use with HyperHDR/Hyperion ambient lighting.

## Requirements

- Rooted LG WebOS TV with [Piccap](https://github.com/webosbrew/piccap) installed
- SSH access enabled on the TV
- SSH key authentication configured between your Kodi device and TV

## Installation

1. Download `script.piccap.zip`
2. In Kodi: **Settings → Add-ons → Install from zip file**
3. Select the downloaded zip file

## SSH Key Setup

Before the add-on will work, you need to set up SSH key authentication:

### On CoreELEC/LibreELEC:

```bash
# Generate SSH key (press Enter for all prompts)
ssh-keygen -t ed25519

# Copy key to your TV (enter TV root password when prompted)
cat ~/.ssh/id_ed25519.pub | ssh root@YOUR_TV_IP "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"

# Test connection (should connect without password)
ssh root@YOUR_TV_IP "echo 'SSH working'"
```

### On other Linux systems:

```bash
ssh-keygen -t ed25519
ssh-copy-id root@YOUR_TV_IP
```

## Configuration

1. Go to **Settings → Add-ons → My add-ons → Program add-ons → Piccap Backlight Toggle → Configure**
2. Enter your TV's IP address
3. Adjust SSH key path if needed (default: `/storage/.ssh/id_ed25519`)

## Usage

### Run directly
- Go to **Add-ons → Program add-ons → Piccap Backlight Toggle**
- Each run toggles the backlight on/off

### Map to remote button
Create a keymap file at `/storage/.kodi/userdata/keymaps/piccap.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<keymap>
  <global>
    <remote>
      <red>RunScript(script.piccap)</red>
    </remote>
  </global>
</keymap>
```

Change `<red>` to your preferred button: `<green>`, `<yellow>`, `<blue>`, `<subtitle>`, etc.

### Available commands

```
RunScript(script.piccap)          # Toggle on/off
RunScript(script.piccap, start)   # Force on
RunScript(script.piccap, stop)    # Force off
RunScript(script.piccap, settings) # Open settings
```

## Troubleshooting

**Add-on shows "Please configure TV IP"**
- Open add-on settings and enter your TV's IP address

**Toggle doesn't work**
- Verify SSH key is set up correctly: `ssh root@YOUR_TV_IP "echo test"`
- Check the SSH key path in settings matches where your key is located
- Check Kodi log: `/storage/.kodi/temp/kodi.log`

**Permission denied errors**
- Regenerate SSH keys and copy to TV again
- Ensure the SSH key path in settings points to your private key (not .pub)

## License

MIT
