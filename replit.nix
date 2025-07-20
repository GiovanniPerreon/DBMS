{ pkgs }:
pkgs.mkShell {
  buildInputs = [
    pkgs.nodejs_23
    pkgs.nodePackages.npm
    pkgs.python3Full
    pkgs.ffmpeg
    pkgs.python3Packages.pip
    pkgs.python3Packages.soundfile
  ];
}