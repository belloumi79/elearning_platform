{ pkgs ? import <nixpkgs> {} }:

let
  python = pkgs.python311;
  pythonPackages = python.pkgs;
in
pkgs.mkShell {
  buildInputs = [
    python
    pythonPackages.flask
    pythonPackages.flask-cors
    pythonPackages.python-dotenv
    pythonPackages.supabase
    pythonPackages.python-multipart
    pythonPackages.passlib
    pythonPackages.python-dateutil
    pythonPackages.psycopg2
    pythonPackages.gunicorn
    pythonPackages.flask-session
    pythonPackages.flask-login
    pythonPackages.flask-migrate
    pythonPackages.flask-bcrypt
    pythonPackages.flask-mail
    pythonPackages.redis
  ];

  shellHook = ''
    # Set up Python environment
    export PYTHONPATH=$PYTHONPATH:$(pwd)
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
      python -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install requirements if needed
    if [ ! -f "requirements.installed" ]; then
      pip install -r requirements.txt
      touch requirements.installed
    fi
    
    echo "Python environment ready!"
    echo "To activate the virtual environment, run: source venv/bin/activate"
  '';
}