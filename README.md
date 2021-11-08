# condaw

>
> a wrapper script that prepares conda environment and (optionally) run doit command for you.
> 
> it's like gradlew, but for conda (& doit)
> 

## Prerequisites

Python is required to run this script, either 2.7 / 3.x would work.

## Install

* download condaw.bat & condaw from the root of the repo
* put it in the root folder of your project
* ignore .condaw in your .gitignore
* profit!

## Usage

```shell
./condaw ...
```

The script will:
* detect whether conda is installed on this machine, and install one locally if not
* create the conda environment(if not exists) and sync its dependencies with environment.yaml
* for the rest of the arguments passed
  * if doit exists in the environment, the rest will be passed to doit command, which means this is equal to doit ...
  * if doit does not exists, the rest will be passed to python, meaning this is equal to python ...

## License

MIT