# Contributing to scaf

### Nix Flake

scaf provides a Nix Flake to install all the required packages for development.
The Nix Flake ensures all developers are using the same versions of all packages
to develop on Scaf in an isolated environment.

Follow the instructions to install
[Nix](https://nixos.org/download/#download-nix) for your OS.

1. Ensure you have a recent version of Nix installed:

Nix Flakes are available in recent versions of Nix. You can check your Nix
version using:

```sh
nix --version
```

If you need to install or update Nix, you can follow the instructions on the Nix
installation page.

2. Enable experimental features:

You need to enable the experimental features in your Nix configuration. To do
this, add the following lines to your ~/.config/nix/nix.conf file. If the file
doesn't exist, you can create it:

```ini
experimental-features = nix-command flakes
```

3. Using Nix Flakes:

Once you have enabled the experimental features, you can use Nix Flakes with the
nix command. For example:

```sh
nix flake show
```

This command will display information about the flake in the current directory
if you have a flake.nix file.

Finally, install [Direnv](https://direnv.net/) and run `direnv allow`. The
direnv configuration in `.envrc` will use the flake to install the required
packages.

### Testing

Run the installer tests from the repository root with Python 3:

```sh
python3 -m unittest discover -s tests -v
```

To test the copier portion of Scaf, run the `./test-scaf.sh` script.

If you are not using the Nix development environment, create a virtual environment and
install black, isort and copier before running `./test-scaf.sh`.

Running `./test-scaf.sh -h` shows the usage instructions:

```shell
Usage: ./test-scaf.sh -t <template_folder> [-o <output_folder>] [-d <test_data>] [-h]
  -t <template_folder> Required: Specify the source folder for the template
  -o <output_folder>   Optional: Specify the output folder (default is /tmp/scaf-test)
  -d <test_data>       Optional: Specify a preset answers data file
  -h                   Show this help message
```
