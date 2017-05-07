# Catalog Management

[![standard-readme compliant](https://img.shields.io/badge/readme%20style-standard-brightgreen.svg?style=flat-square)](https://github.com/RichardLitt/standard-readme)

## Table of Contents
- [Background](#background)
- [Author](#author)
- [How to Use](#how-to-use)
- [Source Files](#source-files)
- [License](#license)

## Background
A very simple catalog management app, demonstrating basic CRUD operations using Flask, SQLAlchemy, Postgresql. It users Materialize for front-end styling.The files in this repository provide a few basic back-end functions to run a swiss pairing tournament, using postgresql db and python.

Note: You may want to install Vagrant and Virtual-Box for running some of these files. 

## Author
[Sejal Parikh](https://in.linkedin.com/in/sejalparikh)

## Frameworks and tools used
1. Materialize - for front-end styling
2. SQLAlchemy - connects and interacts with database using ORM
3. Postgresql - Database system
4. Flask - Python web developement framework

## How to Use
1. Download all the files in the same folder, say 'catalog'.
2. On your terminal, change the path to the catalog folder and do the following to setup your database:
    - `$ vagrant up` (pg_config.sh file contains installation script for all the required packages to run this project.)
    - `$ vagrant ssh`
    - Change the path to the ItemsCatalog directory
    - `$ python database_setup.py`
    - `$ python catalog.py`
4. To view the db schema, run `$ psql catalog`

## Source Files
1. database_setup.py : Creates the postgresql database
2. catalog.py : Contains necessary handlers for all CRUD operations and app navigations.
4. pg_config.sh : Contains scripts to install and setup necessary packages to get the app running.

## License
[GNU General Public License v3](../LICENSE)
