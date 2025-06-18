{ pkgs }: {
  deps = [
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.tesseract
    pkgs.tesseractPackages.tesseract-data-rus
  ];
}
