# BUILD Container
# cd PATH_OF_CESAR_PROJECT_ROOT_CONTAININT_DOCKERFILE

#   docker build -t the-cesar .

# start container an mount the location of your files to /run-files in docker, e.g. mount the root directory from cesar-p-usage-exmaple project.
# if you want to run a different script than basic_cesar_usage.py, change the CMD at the end of the Dockerfile
# make sure to specify absolute path to your project root, otherwise the mounting does not work properly

#    docker run -it -v "PATH_TO_CESAR_PROJECT:/run-files" the-cesar

# The results are stored back to the example folder. They survive even when the container is shut down.

# If you want to get a bash shell in your container to interactively start your scripts, you do:
#    docker run -it -v "PATH_TO_CESAR_PROJECT:/run-files" cesarp bash

# If you change the sources or you want to call another script by editing the Dockerfile you have to re execute the docker build command
# in order that those changes get applied. But it only re builds what is necessary, so installing the dependencies and EnergyPlus is not repeated.
# To change the EnergyPlus Version, you have to edit the Dockerfile or pass EPLUS_VERSION when building the container.

FROM python:3.8-slim-buster

MAINTAINER Leonie Fierz leonie.fierz@empa.ch

# This is not ideal. The tarballs are not named nicely and EnergyPlus versioning is strange
#ARG ENERGYPLUS_VERSION=8.5.0
#ARG ENERGYPLUS_TAG=v8.5.0
#ARG ENERGYPLUS_SHA=c87e61b44b
#ARG ENERGYPLUS_INSTALL_VERSION=8-5-0
#ARG ENERGYPLUS_INSTALL_SYMLINK_VERSION=8-5
ARG ENERGYPLUS_VERSION=9.3.0
ARG ENERGYPLUS_TAG=v9.3.0
ARG ENERGYPLUS_SHA=baff08990c
ARG ENERGYPLUS_INSTALL_VERSION=9-3-0
ARG ENERGYPLUS_INSTALL_SYMLINK_VERSION=9-3
ARG POETRY_VERSION=1.0.3
ENV ENERGYPLUS_VERSION=$ENERGYPLUS_VERSION
ENV ENERGYPLUS_TAG=v$ENERGYPLUS_VERSION
ENV ENERGYPLUS_SHA=$ENERGYPLUS_SHA

# This should be x.y.z, but EnergyPlus convention is x-y-z
ENV ENERGYPLUS_INSTALL_VERSION=$ENERGYPLUS_INSTALL_VERSION

# update packages
RUN pip install "poetry==$POETRY_VERSION" \
    && poetry config virtualenvs.create true \
    && poetry config --local virtualenvs.in-project false

# INSTALL EnergyPlus
# Downloading from Github
ENV ENERGYPLUS_DOWNLOAD_BASE_URL https://github.com/NREL/EnergyPlus/releases/download/$ENERGYPLUS_TAG
ENV ENERGYPLUS_DOWNLOAD_FILENAME EnergyPlus-$ENERGYPLUS_VERSION-$ENERGYPLUS_SHA-Linux-x86_64.sh
ENV ENERGYPLUS_DOWNLOAD_URL $ENERGYPLUS_DOWNLOAD_BASE_URL/$ENERGYPLUS_DOWNLOAD_FILENAME

# System deps:
# Collapse the update of packages, download and installation into one command
# to make the container smaller & remove a bunch of the auxiliary apps/files
# that are not needed in the container
RUN apt-get update && apt-get install -y ca-certificates curl git \
    && curl -SLO $ENERGYPLUS_DOWNLOAD_URL \
    && chmod +x $ENERGYPLUS_DOWNLOAD_FILENAME \
    && echo "y\r" | ./$ENERGYPLUS_DOWNLOAD_FILENAME \
    && rm $ENERGYPLUS_DOWNLOAD_FILENAME \
    && cd /usr/local/EnergyPlus-$ENERGYPLUS_INSTALL_VERSION \
    && rm -rf DataSets Documentation ExampleFiles WeatherData MacroDataSets PostProcess/convertESOMTRpgm \
    PostProcess/EP-Compare PreProcess/FMUParser PreProcess/ParametricPreProcessor PreProcess/IDFVersionUpdater \
	  && ln -s /usr/local/EnergyPlus-$ENERGYPLUS_INSTALL_VERSION /usr/local/EnergyPlus-$ENERGYPLUS_INSTALL_SYMLINK_VERSION
RUN apt-get remove --purge -y curl ca-certificates \
    && apt-get autoremove -y --purge \
	  # Remove the broken symlinks
	  && cd /usr/local/bin \
	  && find -L . -type l -delete \
	  && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/local/cesar
ENV TEMP=/tmp/

COPY poetry.lock pyproject.toml ./
RUN poetry install --no-root --no-dev --no-interaction

COPY . . 
RUN poetry install --no-dev --no-interaction \
    && rm -rf ./tests \
    && rm -rf ./docs

CMD [ "poetry", "run", "python3", "/run-files/basic_cesar_usage.py"]

