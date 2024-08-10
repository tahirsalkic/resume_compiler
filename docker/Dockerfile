# Use an official Python runtime as a parent image
FROM python:3.10

# Install necessary packages and dependencies
RUN apt-get update && apt-get install -y \
    # Install Firefox Extended Support Release
    firefox-esr \
    # Install wget utility for downloading files
    wget \
    # Install dialog utility for creating TUI dialogs
    dialog \
    # Install LibreOffice for document conversions
    libreoffice \
    # Install unoconv for document conversions
    unoconv \
    # Allow 'apt' to use repositories accessed via HTTPS
    apt-transport-https \
    # Download and set up GeckoDriver for Selenium
    && wget https://github.com/mozilla/geckodriver/releases/download/v0.34.0/geckodriver-v0.34.0-linux64.tar.gz \
    # Extract the downloaded tarball
    && tar -xvzf geckodriver-v0.34.0-linux64.tar.gz \
    # Make GeckoDriver executable
    && chmod +x geckodriver \
    # Move GeckoDriver to a directory in the PATH
    && mv geckodriver /usr/local/bin/ \
    # Remove the tarball to clean up
    && rm geckodriver-v0.34.0-linux64.tar.gz \
    # Add Debian contrib repository and install Microsoft TrueType core fonts
    && echo "deb http://deb.debian.org/debian/ bookworm contrib" | tee -a /etc/apt/sources.list.d/contrib.list \
    && apt-get update \
    # Install Microsoft TrueType core fonts
    && apt-get install -y ttf-mscorefonts-installer \
    # Clean up the local repository of retrieved package files
    && apt-get clean \
    # Remove the lists of available packages to save space
    && rm -rf /var/lib/apt/lists/*

# Configure Git with user information
RUN git config --global user.name "Tahir Salkic" \
    && git config --global user.email "tahirsalkic@gmail.com"

# Create a Firefox profile for headless mode
RUN firefox -headless -CreateProfile "root"