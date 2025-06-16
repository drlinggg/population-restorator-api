# population-restorator-api

# Installation:
```
git clone github.com/drlinggg/population-restorator-api
cd population-restorator-api
make install (pipx install .)
```
or
```
install git+https://drlinggg/population_restorator-api
```
# Running:
Remove .example from .yaml file and configure the changes (for e.x. add new paths for loggers, disable debug mode).

Then you can use poetry to run application
```
poetry run launch_population-restorator-api
```

## population_restorator
Used inside to forecast population
This utility can be used to balance city houses population in 3 steps:
- settle people to dwellings useing total city population and houses living area
- divide people in houses to ages and social groups using number of people and variances values to
- forecast the people number over the following years depending on scenario


## Develpment

1. Install poetry and prepare environment (`pipx install poetry`; `poetry install --with dev`; `poetry shell`)
2. Initialize pre-commit by running `pre-commit install`
3. Make changes to the code in a separate branch or repository (`git checkout -b <branch-name>`)
4. Before commit, run `make format lint` to auto-format your code and check it with pylint
5. Commit your changes
6. Create pull-request to _dev_ branch