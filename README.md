# Telegram-IMDbot
Set alerts for your favorite IMDb movies or series.

A Telegram bot which enables the user to search movie or series titles on IMDb.com, set alerts for the chosen result and receive a notification via Telegram
when the respective movie or new series episode is out.

## Python Libraries

You will require the [python-telegram-bot](https://python-telegram-bot.org/) library to use Telegram and the [IMDbPy](https://pypi.org/project/IMDbPY/) library to query IMDb.com.

## Telegram Bot

 You will need to create a Telegram bot and edit the python script to add your personal bot token.
 
 Details on how to create a bot [here](https://core.telegram.org/bots#creating-a-new-bot).
 
 The bot has to be configured as a [inline bot](https://core.telegram.org/bots/inline) with feedback collection enabled.

## Description

* requirements.txt

  This file contains all the python libraries needed to run the bot.

* utils/db.py 

  This python module is used to perform CREATE/READ/UPDATE/DELETE operations on the bot's database.
  The bot usees the python built in sqlite3 library to create a database used to store the user's titles and release dates.

* utils/movie.py

  This python module is used to query IMDb.com using the [IMDbPy](https://pypi.org/project/IMDbPY/) library and find the movie or series next episode release date.

* imdbot.py

  This is the actual inline Telegram bot.

* database

  The directory where the database is created at the first script run.

* imdbot.service

  Systemd service file for the bot.

## Setup your personal Telegram IMDbot

  1. Clone this repository

    # cd /opt
	# git clone https://github.com/Matei-Ciobotaru/Telegram-IMDbot.git

  2. Create the python virtual environment

    # cd Telegram-IMDbot
    # python3 -m venv venv

  3. Activate the virtual env and install the required dependencies

    # . venv/bin/activate
    # pip install -r ./requirments.txt

  4. Configure your bot details. Replace the "TOKEN" global variable with your secret Telegram bot token.

    # vim imdbot.py

  5. Run the script (default log file location is "/var/log/imdbot.log")

    # chmod 755 ./imdbot.py
    # ./imdbot.py

  Optional:

  6. Create systemd service using the 'imdbot.service' file:

    # sudo cp -p ./imdbot.service /lib/systemd/system/imdbot.service
    # sudo systemctl daemon-reload
    # sudo systemctl enable imdbot

  7. Start the bot

    # systemctl start imdbot

## Use my Telegram IMDbot

**Open telegram and search for "ximdbot", select "START" and enjoy!(video example)**<br>
   
<a href="http://www.youtube.com/watch?feature=player_embedded&v=_Bq7RveSv9M
" target="_blank"><img src="http://img.youtube.com/vi/_Bq7RveSv9M/0.jpg" 
alt="Video example" width="240" height="180" border="10" /></a>


**New episode Telegram notification**<br>

<img src="https://i.imgur.com/ff6Ineg.jpg" height="650" width="350">

