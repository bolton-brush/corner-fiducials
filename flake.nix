{
  description = "corner-fiducials deterministic AAOF image-analysis development shell";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
    in {
      devShells = forAllSystems (system:
        let
          pkgs = import nixpkgs { inherit system; };
          python = pkgs.python3.withPackages (ps: with ps; [
            numpy opencv4 scipy pytest build setuptools wheel invoke twine pillow
          ]);
        in {
          default = pkgs.mkShell {
            packages = [ python ];
            shellHook = ''
              export PYTHONPATH="$PWD/src''${PYTHONPATH:+:$PYTHONPATH}"
              echo "corner-fiducials: invoke test; invoke build --no-isolation; invoke check"
            '';
          };
        });
    };
}
