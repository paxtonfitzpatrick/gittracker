# deactivate travis-provided virtual environment on linux to set up conda instead
if [[ "$TRAVIS_OS_NAME" == "linux" ]]
then
  deactivate
fi

# set conda path
echo "setting conda path"
export MINICONDA_PATH="$HOME"/miniconda
export MINICONDA_LIB_BIN_PATH=$MINICONDA_PATH/Library/bin

if [[ "$TRAVIS_OS_NAME" == "windows" ]]
then
  export MINICONDA_SUB_PATH=$MINICONDA_PATH/Scripts
  export MINICONDA_PATH_WIN=`cygpath --windows $MINICONDA_PATH`
else
  export MINICONDA_SUB_PATH=$MINICONDA_PATH/bin
fi

# download miniconda installer if not running Windows
# (Windows will use choco to install miniconda instead)
if [[ "$TRAVIS_OS_NAME" == "linux" ]]
then
  mkdir -p "$HOME"/download
  echo "downloading miniconda installer for linux"
  wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O "$HOME"/download/miniconda.sh
elif [[ "$TRAVIS_OS_NAME" == "osx" ]]
then
  mkdir -p "$HOME"/download
  echo "downloading miniconda installer for MacOS"
  wget https://repo.continuum.io/miniconda/Miniconda3-latest-MacOSX-x86_64.sh -O "$HOME"/download/miniconda.sh
fi
