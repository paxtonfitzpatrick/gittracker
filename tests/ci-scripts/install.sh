# install miniconda
if [[ "$TRAVIS_OS_NAME" == "windows" ]]
then
  echo "installing miniconda for windows"
  choco install miniconda3 --params="'/JustMe /AddToPath:1 /D:$MINICONDA_PATH_WIN'"
else
  echo "installing miniconda for posix"
  bash "$HOME"/download/miniconda.sh -b -u -p "$MINICONDA_PATH"
fi

# update path
export PATH="$MINICONDA_PATH:$MINICONDA_SUB_PATH:$MINICONDA_LIB_BIN_PATH:$PATH"

source $MINICONDA_PATH/etc/profile.d/conda.sh
hash -r
conda config --set always_yes yes --set changeps1 no
conda update -q conda
# Useful for debugging any issues with conda
conda info -a

# create and activate conda environment
echo "running in ${TRAVIS_OS_NAME} environment"
echo "creating environment with Python ${PYTHON_VERSION}"
conda create -q -n test-environment --yes python="$PYTHON_VERSION" pip pytest
conda activate test-environment
# install package with pip to test pip installation process
pip install --quiet --upgrade pip
pip install .
