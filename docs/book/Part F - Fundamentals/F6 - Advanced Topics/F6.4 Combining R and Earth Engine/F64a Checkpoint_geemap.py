import ee 
import geemap

Map = geemap.Map()

#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Chapter:      F6.4 Combining R and Earth Engine
#  Checkpoint:   F64a
#  Authors:      Cesar Aybar, David Montero, Antony Barja, Fernando Herrera, Andrea Gonzales, and Wendy Espinoza
#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

'Comment from Ellen':
If possible,  perhaps put this into a checkpoint? Also,  one option (if links are allowed in that), 'to refer to the link': 'https':
Installation is always tricky.
'Till today I am still having issue with the Anaconda install in Windows' :).

Installing rgee can be challenging, since it has dependencies in both R and Python. Thanks to the fantastic work of CRAN managing R packages, installation in R should not be a problem. Nevertheless, some difficulties can appear when users try to connect both languages. If you are a new Python user, we recommend using the built-in ee_install function. In Rstudio, press Ctrl + Enter (or just Enter on macOS) to execute the code line by line.

library(rgee)
'rgee':'':ee_install()


'The ee_install function will set up everything for you. In short, it performs the following tasks': (1) Creating a Python environment, (2) creating an environment variable, EARTHENGINE_PYTHON, that stores your Python interpreter path (which will help rgee know where to look the next time you log in), and (3) installing the dependencies in the previously created environment. Alternatively, users who want to use their own Python environment could run, instead of ee_install, one of the following options, depending on their operating system.

# IMPORTANT: Change 'py_path' argument according to your own Python PATH
## For Anaconda users - Windows OS
## Anaconda users must run "where anaconda" in the console.
win_py_path = paste0(
"C:/Users/UNICORN/AppData/Local/Programs/Python/",
"Python37/python.exe"
)
ee_install_set_pyenv(
py_path = win_py_path
py_env = NULL 
)

## For Anaconda users - MacOS users
## Anaconda users must run "where anaconda" in the console.
ee_install_set_pyenv(
py_path = "/Users/UNICORN/opt/anaconda3/bin/python"
py_env = NULL 
)

## For Miniconda users - Windows OS
win_py_path = paste0(
"C:/Users/UNICORN/AppData/Local/r-miniconda/envs/rgee/",
"python.exe"
)
ee_install_set_pyenv(
py_path = win_py_path
py_env = "rgee" 
)

## For Miniconda users - Linux/MacOS users
unix_py_path = paste0(
"/home/UNICORN/.local/share/r-miniconda/envs/",
"rgee/bin/python3"
)
ee_install_set_pyenv(
py_path = unix_py_path
py_env = "rgee" 
)

## For virtualenv users - Linux/MacOS users
ee_install_set_pyenv(
py_path = "/home/UNICORN/.virtualenvs/rgee/bin/python"
py_env = "rgee" 
)

## For Python root user - Linux/MacOS users
ee_install_set_pyenv(
py_path = "/usr/bin/python3"
py_env = NULL
Renviron = "global" 
)

ee_install_set_pyenv(
py_path = "/usr/bin/python3"
py_env = NULL
Renviron = "local" 
)


'Regardless of whether you are using ee_install or ee_install_set_pyenv, this only needs to be run once. Also, take into account that the Python PATH you set must have installed the rgee Python dependencies. The use of Miniconda/Anaconda is mandatory for Windows users; Linux and MacOS users could instead use virtualenv. After setting up your Python environment, you can use the function below to check the status of rgee. If you find any issue in the installation procedure, consider opening an issue at https':

ee_check() 




Enter the link below into your browser to see how your code should look at this point

'https':


'Note from Ellen below': "Congratulationsnot  You have successfully deployed the Earth Engine App on Heroku. "
 'Does not work although I followed the instructions':'). https':
Author will have to test. I can test it if desired. Others are also welcome to test this.
Was tested and closed by author in beginning of March. Feel bad that is happening right now.
@jeffcardille@gmail.com
Show less
Hi, I am also tagging  Quisheng @qwu18@utk.edu here.  Perhaps this got missed due to the editing comments. Hi Qiusheng, I ran into an issue here. Can you please check once more please? Thanks.


#  -----------------------------------------------------------------------
#  CHECKPOINT
#  -----------------------------------------------------------------------


Map