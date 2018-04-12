tweet_fetcher_readme.md

Introduction
------------

Tweet_fetcher is an application which establishes a tweet stream using the Twitter API, filters out tweets containing earthquake keywords, and adds these tweets to a Postgres table.

Installation and Dependencies
-----------------------------

The ted conda environment must be activated for whichever user is running PDL. The PDL runs this code when a new event or event update (origin product) is received. To activate this environment for that user, type:
    source activate ted
If the environment has not been created yet or does not exist, type:
    ./install.sh 

Tweet_fetcher has been designed to run in Python 3.

Running tweet_fetcher.py
------------------------

Run tweet_fetcher as a background process by typing:
    python tweet_fetcher &
