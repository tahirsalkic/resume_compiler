# Use an official Python runtime as a parent image
FROM python:3.10

# Install Firefox, wget, and additional dependencies for unoconv
RUN apt-get update && apt-get install -y \
    firefox-esr \                     # Install Firefox Extended Support Release
    wget \                            # Install wget utility for downloading files
    dialog \                          # Install dialog utility (used for creating TUI dialogs)
    libreoffice \                     # Install LibreOffice (required by unoconv)
    unoconv \                         # Install unoconv for converting between document formats
    apt-transport-https \             # Install package to allow 'apt' to use repositories accessed via HTTPS
    # Download and set up GeckoDriver for Selenium
    && wget https://github.com/mozilla/geckodriver/releases/download/v0.34.0/geckodriver-v0.34.0-linux64.tar.gz \
    && tar -xvzf geckodriver* \       # Extract the downloaded tarball
    && chmod +x geckodriver \         # Make GeckoDriver executable
    && mv geckodriver /usr/local/bin/ \ # Move GeckoDriver to a directory in the PATH
    && rm geckodriver-v0.34.0-linux64.tar.gz \ # Remove the tarball to clean up
    # Add Debian contrib repository and install Microsoft TrueType core fonts
    && echo "deb http://deb.debian.org/debian/ bookworm contrib" | tee -a /etc/apt/sources.list.d/contrib.list \
    && apt-get update \
    && apt-get install -y ttf-mscorefonts-installer \ # Install Microsoft TrueType core fonts
    && apt-get clean \                # Clean up the local repository of retrieved package files
    && rm -rf /var/lib/apt/lists/*    # Remove the lists of available packages to save space

# Create a Firefox profile to leverage cookies from local firefox
RUN firefox -headless -CreateProfile "root"
