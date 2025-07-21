{ pkgs }: {
  deps = [
    pkgs.ffmpeg
    pkgs.python311Full
    pkgs.nodejs
    pkgs.nodePackages.npm
    pkgs.python311Packages.soundfile
  ];
}