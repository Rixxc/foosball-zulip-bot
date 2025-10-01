# Nix Flake Setup

This project is now available as a Nix flake with systemd service support.

## Quick Start (Development)

```bash
# Enter development shell
nix develop

# Run the bot (after configuring .env)
python main.py
```

## Running as a NixOS Service

### 1. Add the flake to your NixOS configuration

In your `flake.nix`:

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    zulip-foosball-bot = {
      url = "path:/path/to/this/repo";
      # or use git: url = "git+https://...";
    };
  };

  outputs = { self, nixpkgs, zulip-foosball-bot }: {
    nixosConfigurations.yourhost = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      modules = [
        zulip-foosball-bot.nixosModules.default
        ./configuration.nix
      ];
    };
  };
}
```

### 2. Create environment file

Create `/etc/zulip-foosball-bot/env` with your credentials:

```bash
ZULIP_EMAIL=your-bot@your-zulip-server.com
ZULIP_API_KEY=your-api-key-here
ZULIP_SITE=https://your-zulip-server.com
```

Set appropriate permissions:

```bash
sudo chmod 600 /etc/zulip-foosball-bot/env
sudo chown zulip-foosball-bot:zulip-foosball-bot /etc/zulip-foosball-bot/env
```

### 3. Enable the service in configuration.nix

```nix
{
  services.zulip-foosball-bot = {
    enable = true;
    environmentFile = "/etc/zulip-foosball-bot/env";
    # Optional: customize user/group
    # user = "zulip-foosball-bot";
    # group = "zulip-foosball-bot";
  };
}
```

### 4. Rebuild and start

```bash
sudo nixos-rebuild switch
sudo systemctl status zulip-foosball-bot
```

## Service Management

```bash
# View logs
sudo journalctl -u zulip-foosball-bot -f

# Restart service
sudo systemctl restart zulip-foosball-bot

# Stop service
sudo systemctl stop zulip-foosball-bot

# Check status
sudo systemctl status zulip-foosball-bot
```

## Running Without NixOS

You can still use the flake on non-NixOS systems:

```bash
# Build the package
nix build

# Run directly
nix run

# Or install it
nix profile install
```

## Configuration Options

- `services.zulip-foosball-bot.enable` - Enable the service (default: false)
- `services.zulip-foosball-bot.environmentFile` - Path to environment file (required)
- `services.zulip-foosball-bot.user` - Service user (default: "zulip-foosball-bot")
- `services.zulip-foosball-bot.group` - Service group (default: "zulip-foosball-bot")

## Security Features

The systemd service includes hardening options:
- Runs as dedicated non-root user
- Read-only system directories
- Private /tmp and /dev
- No privilege escalation
- Restricted system calls
