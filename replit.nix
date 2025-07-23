{ pkgs }: {
  deps = [
    pkgs.ffmpeg-full
    pkgs.libopus
    pkgs.ffmpeg
    pkgs.python311Full
    pkgs.nodejs
    pkgs.nodePackages.npm
    pkgs.python311Packages.soundfile
  ];
}