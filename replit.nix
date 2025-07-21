{ pkgs }:
pkgs.mkShell {
  buildInputs = [
    pkgs.python311
    pkgs.nodejs_23
    pkgs.nodePackages.npm
    pkgs.python3Full
    pkgs.ffmpeg
    pkgs.python3Packages.pip
    pkgs.python3Packages.soundfile
  ];
}