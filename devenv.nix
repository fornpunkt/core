{ pkgs, lib, config, ... }:

{
  languages.python = {
    enable = true;
    version = "3.11.7";
    venv = {
      enable = true;
      requirements = ./requirements.txt;
    };
  };

  dotenv.enable = true;

  scripts = {
    setup.exec = ''
      python -Wa manage.py migrate
    '';

    run.exec = ''
      python -Wa manage.py runserver "$@"
    '';

    test.exec = ''
      python -Wa manage.py test "$@"
    '';

    manage.exec = ''
      python -Wa manage.py "$@"
    '';
  };

  enterShell = ''
    echo "FornPunkt development environment"
    echo ""
    echo "Available commands:"
    echo "  setup   - run database migrations"
    echo "  run     - start the development server"
    echo "  test    - run the test suite"
    echo "  manage  - wrapper for manage.py"
  '';
}
