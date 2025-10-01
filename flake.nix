{
  description = "Zulip Foosball Bot - A matchmaking bot for foosball games";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    let
      # System-independent outputs (NixOS module)
      nixosModules.default = { config, lib, pkgs, ... }:
        with lib;
        let
          cfg = config.services.zulip-foosball-bot;
        in
        {
          options.services.zulip-foosball-bot = {
            enable = mkEnableOption "Zulip Foosball Bot service";

            environmentFile = mkOption {
              type = types.path;
              description = ''
                Path to file containing environment variables for the bot.
                Should contain ZULIP_EMAIL, ZULIP_API_KEY, and ZULIP_SITE.
                See .env.example for reference.
              '';
              example = "/etc/zulip-foosball-bot/env";
            };

            user = mkOption {
              type = types.str;
              default = "zulip-foosball-bot";
              description = "User account under which the bot runs";
            };

            group = mkOption {
              type = types.str;
              default = "zulip-foosball-bot";
              description = "Group under which the bot runs";
            };
          };

          config = mkIf cfg.enable {
            systemd.services.zulip-foosball-bot = {
              description = "Zulip Foosball Bot";
              after = [ "network-online.target" ];
              wants = [ "network-online.target" ];
              wantedBy = [ "multi-user.target" ];

              serviceConfig = {
                Type = "simple";
                User = cfg.user;
                Group = cfg.group;
                Restart = "always";
                RestartSec = "10s";
                EnvironmentFile = cfg.environmentFile;
                ExecStart = "${self.packages.${pkgs.system}.default}/bin/zulip-foosball-bot";

                # Security hardening
                ProtectSystem = "strict";
                ProtectHome = true;
                NoNewPrivileges = true;
                PrivateTmp = true;
                PrivateDevices = true;
                ProtectKernelTunables = true;
                ProtectControlGroups = true;
                RestrictRealtime = true;
                RestrictSUIDSGID = true;
                LockPersonality = true;
              };
            };

            users.users.${cfg.user} = mkIf (cfg.user == "zulip-foosball-bot") {
              isSystemUser = true;
              group = cfg.group;
              description = "Zulip Foosball Bot service user";
            };

            users.groups.${cfg.group} = mkIf (cfg.group == "zulip-foosball-bot") { };
          };
        };
    in
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python3;
        pythonPackages = python.pkgs;

        zulip-foosball-bot = pythonPackages.buildPythonApplication {
          pname = "zulip-foosball-bot";
          version = "0.1.0";

          src = ./.;

          propagatedBuildInputs = with pythonPackages; [
            zulip
            python-dotenv
          ];

          format = "other";

          installPhase = ''
            mkdir -p $out/bin $out/share/zulip-foosball-bot

            # Copy all Python files
            cp *.py $out/share/zulip-foosball-bot/

            # Copy .env.example
            cp .env.example $out/share/zulip-foosball-bot/

            # Create wrapper script with proper PYTHONPATH
            cat > $out/bin/zulip-foosball-bot <<EOF
            #!${pkgs.bash}/bin/bash
            export PYTHONPATH="$PYTHONPATH"
            cd $out/share/zulip-foosball-bot
            exec ${python}/bin/python main.py "\$@"
            EOF

            chmod +x $out/bin/zulip-foosball-bot
          '';

          meta = with pkgs.lib; {
            description = "Zulip bot for foosball matchmaking";
            license = licenses.mit;
            maintainers = [ ];
          };
        };

      in
      {
        packages = {
          default = zulip-foosball-bot;
          zulip-foosball-bot = zulip-foosball-bot;
        };

        apps = {
          default = {
            type = "app";
            program = "${zulip-foosball-bot}/bin/zulip-foosball-bot";
          };
        };

        devShells.default = pkgs.mkShell {
          buildInputs = with pythonPackages; [
            python
            zulip
            python-dotenv
          ];

          shellHook = ''
            echo "Zulip Foosball Bot Development Environment"
            echo "=========================================="
            echo ""
            echo "Commands:"
            echo "  python main.py    - Run the bot"
            echo ""
            echo "Setup:"
            echo "  1. Copy .env.example to .env"
            echo "  2. Configure your Zulip credentials in .env"
            echo "  3. Run: python main.py"
            echo ""
          '';
        };
      }
    ) // { inherit nixosModules; };
}
