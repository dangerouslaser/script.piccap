# Piccap Backlight Toggle for Kodi

Toggle the Piccap screen capture service on rooted LG WebOS TVs for use with HyperHDR/Hyperion ambient lighting.

## Requirements

- Rooted LG WebOS TV with [Piccap](https://github.com/webosbrew/piccap) installed
- SSH access enabled on the TV

## Installation

1. Download `script.piccap.zip` from the [latest release](https://github.com/dangerouslaser/script.piccap/releases/latest)
2. In Kodi: **Settings → Add-ons → Install from zip file**
3. Select the downloaded zip file

## Setup

The add-on includes a **guided setup wizard** that launches automatically on first run. It will:

1. **Discover your TV** — scans the network via SSDP and lists found LG TVs (or lets you enter an IP manually)
2. **Generate an SSH key** — creates an ed25519 key if one doesn't exist
3. **Copy the key to your TV** — prompts for the TV's root password and installs the key
4. **Test the connection** — verifies everything works

You can re-run the wizard at any time from **Add-on Settings → Setup → Run Setup Wizard**.

### Manual setup (optional)

If you prefer to configure things manually:

```bash
# Generate SSH key
ssh-keygen -t ed25519

# Copy key to your TV
cat ~/.ssh/id_ed25519.pub | ssh root@YOUR_TV_IP "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

Then open the add-on settings and enter your TV's IP address and SSH key path.

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
RunScript(script.piccap)           # Toggle on/off
RunScript(script.piccap, start)    # Force on
RunScript(script.piccap, stop)     # Force off
RunScript(script.piccap, setup)    # Run setup wizard
RunScript(script.piccap, settings) # Open settings
```

## Troubleshooting

**Toggle doesn't work**
- Re-run the setup wizard from add-on settings
- Verify SSH key is set up correctly: `ssh root@YOUR_TV_IP "echo test"`
- Check the SSH key path in settings matches where your key is located
- Check Kodi log: `/storage/.kodi/temp/kodi.log`

**Permission denied errors**
- Re-run the setup wizard — it will detect the failed connection and offer to re-copy the key
- Ensure the SSH key path in settings points to your private key (not .pub)

## License

MIT
