Hyppy
=====

A Python interface for the `Hyperiums <http://www.hyperiums.com>`_ API (HAPI).

Aims to provide:

-   A HAPI wrapper, allowing multiple connections (i.e. per user, per game),
-   Parsing tools for daily list exports,
-   Functions and formulae for some of the game's mechanics.

MIT licensed.

Installation and quickstart
---------------------------

To install::

    pip install hyppy

Using the HAPI::

    from hyppy.hapi import HAPI

    hapi = HAPI('Hyperiums6')

    # Get a list of games
    print hapi.games()

    # Password authentication for list downloads
    hapi.authenticate_basic('loginname', 'password')

    # Download today's planet list for this game
    hapi.download('planets', './planets.txt.gz')

    # HAPI key authentication for everything else
    hapi.authenticate_hapi('loginname', 'hapikey')
    
    # Get all player's planets
    print hapi.planet()
