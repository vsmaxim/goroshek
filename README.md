Goroshek telegram bot
=====================

**Goroshek** is the telegram bot that helps you manage your university information page. 

## Installation and configuration

Complete following steps to install and configure your bot:

1. Install with poetry - `poetry install`
1. Run `cp .env.template .env` and edit `.env` file with you configurations
1. Run `cp admins.example.json admins.json` and `cp students.example.json students.json` and
edit them for your needs.
1. Place your google application (with Calendar API enabled) `credentials.json` in root folder

## Run

To run this bot simply use `poetry run python -m goroshek`
