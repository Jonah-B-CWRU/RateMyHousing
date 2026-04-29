{
  description = "A Python project with FastAPI and a development shell for VS Code";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};

      # Define the specific Python version (e.g., python311, python312)
      pythonPackage = pkgs.python313;
      pythonDeps = p: with p; [
        # Web API
        fastapi
        uvicorn
        jinja2
        python-multipart

        # firebase intigration
        firebase-admin
        google-cloud-firestore
        protobuf

        # testing
        pytest
        coverage
        pdoc
      ];

      # Create a custom Python environment
      pythonEnv = pythonPackage.withPackages pythonDeps;

    in {
      devShells.${system}.default = pkgs.mkShell {
        # Packages available in the shell, primarily development tools
        packages = [
          pythonEnv  # The custom Python environment
          pkgs.git
          pkgs.python313Packages.pip-tools
        ];

        # Environment variables for shell startup
        sshellHook = ''
          echo "Entering development shell..."
          
          # Add the current working directory to the PYTHONPATH (FIX)
          export PYTHONPATH="$PWD:$PYTHONPATH" 

          # Set the VIRTUAL_ENV variable to trick VS Code's Python extension
          export VIRTUAL_ENV="$PWD/.venv-flake"
          
          # This creates a dummy directory that the Python extension looks for.
          mkdir -p .venv-flake
          
          # Optional: Add the local site-packages to the PYTHONPATH (if needed)
          # export PYTHONPATH="${pythonEnv}/lib/${pythonPackage.libPrefix}/site-packages:$PYTHONPATH"
        '';
      };
    };
}