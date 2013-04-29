import re
import time
import logging
import requests


__logname__ = 'hyppy'

def requires_password_auth(fn):
    """Decorator for HAPI methods that requires the instance to be authenticated with a password"""
    def wrapper(self, *args, **kwargs):
        self.auth_context = HAPI.auth_context_password
        return fn(self, *args, **kwargs)
    return wrapper


def requires_api_auth(fn):
    """Decorator for HAPI methods that requires the instance to be authenticated with a HAPI token"""
    def wrapper(self, *args, **kwargs):
        self.auth_context = HAPI.auth_context_hapi
        return fn(self, *args, **kwargs)
    return wrapper


class HAPI(object):
    """
    The HAPI service object - handles requests and authentication.
    Most methods return a HAPIResponse object.

    Methods decorated with a requires_*_auth wrapper ensure that the relevant authentication credentials have been
    stored and are passed into the request. One caveat of this implementation is that it will not cleanly support
    endpoints that allow multiple authentication methods. Something to look at if such an endpoint is created.
    """
    default_url = 'http://www.hyperiums.com/servlet/HAPI'

    auth_context_hapi = 'hapi'
    auth_context_password = 'password'

    """
    game - A game name, such as Hyperiums6, or HyperiumsRLF. See results of HAPI.games().
           Required for most requests (except games()
    base_url - For use with a compatible API on a different domain (i.e. a self-hosted cache)
    cachebreak - If a response does not indicate that it is uncached a warning log will be emitted.
    """
    def __init__(self, game=None, base_url=None, cachebreak=True):
        self.base_url = base_url if base_url is not None else HAPI.default_url
        self.game = game
        self.cachebreak = cachebreak

        self.auth_context = None
        self.credentials = {}

    """
    Password authentication
    Stores the current game (set in __init__), and the player's credentials for requests requiring password auth
    """
    def authenticate_basic(self, username, password):
        self.credentials[HAPI.auth_context_password] = {
            'game': self.game,
            'player': username,
            'passwd': password
        }

    """
    HAPI authentication
    Authenticates with the given HAPI credentials to the game (set in __init__) and stores the returned token for
    requests that require HAPI auth.
    """
    def authenticate_hapi(self, username, hapikey):
        res = self.get(game=self.game, player=username, hapikey=hapikey)

        self.credentials[HAPI.auth_context_hapi] = {
            'gameid': res.gameid,
            'playerid': res.playerid,
            'authkey': res.authkey
        }

        return res

    """
    Build a url

    **kwargs will be put in the request's query string.
    Will merge the relevant authentication credentials into the query string set depending on the decorator used.

    Yes, password-auth-based requests will send the password in the clear in the URI. I expect they're stored clear-text
    at the other end as well. I recommend creating another account for your list downloads.
    """
    def build_url(self, **kwargs):
        params = kwargs

        if self.auth_context is not None:
            if self.auth_context not in self.credentials:
                raise ValueError("Authentication credentials for context %s have not been stored" % self.auth_context)
            else:
                params = dict(params.items() + self.credentials[self.auth_context].items())

        cachebreaker = None
        if self.cachebreak:
            cachebreaker = int(time.time())
            params['failsafe'] = cachebreaker


        url = self.base_url + "?" + "&".join(["%s=%s" % (k, v) for k, v in params.iteritems()])
        return url

    """
    Make a request


    If cache breaking is turned on, a failsafe parameter will be present in the returned HAPIResponse.
    """
    def get(self, **kwargs):
        url = self.build_url(kwargs)
        req = requests.get(url)

        result = HAPIResponse(req.text)

        if self.cachebreak and ('failsafe' not in result or result.failsafe != cachebreaker):
            logging.getLogger(__logname__).warning("Response returned is possibly outdated (no cachebreaker returned)")

        return result

    def games(self):
        return self.get("games")

    @requires_api_auth
    def planet(self, planet=None, data=None):
        types = ("trading", "infiltr", "general")

        # Default arguments
        if planet is None:
            planet = "*"
        if data is None:
            data = "general"

        if data not in types:
            raise ValueError("Invalid data type %s (valid: %s)" % (data, ", ".join(types)))

        return self.get(request="getplanetinfo", planet=planet, data=data)

    @requires_api_auth
    def fleet(self, planet=None, data=None):
        types = ("own_planets", "foreign_planets")

        # Default arguments
        if planet is None:
            planet = "*"
        if data is None:
            data = "own_planets"

        if data not in types:
            raise ValueError("Invalid data type %s (valid: %s)" % (data, ", ".join(types)))

        return self.get(request="getfleetsinfo", planet=planet, data=data)

    @requires_api_auth
    def exploitations(self):
        return self.get(request="getexploitations")

    @requires_api_auth
    def alliance_planets(self, tag, start=0):
        tag = tag.strip('[]')

        return self.get(request="getallianceplanets", tag=tag, start=start)


    @requires_password_auth
    def download(self, type, local_path):
        types = ('players', 'planets', 'events', 'alliances')
        if type not in types:
            raise ValueError("Invalid list type %s (valid: %s)" % (type, ", ".join(types)))

        # Custom getter as response retrieves a file
        url = self.build_url(request="download", filetype=type)
        res = requests.get(url, stream=True)
        # TODO: When response returns a non-200 status code check that

        with open(local_path, 'w') as out:
            for chunk in res.iter_content():
                out.write(chunk)

        return local_path

class HAPIResponse(object):
    def __init__(self, response):
        self.data = HAPIResponse.parse(response)

    def __getattr__(self, item):
        return self.data[item]

    @staticmethod
    def parse(response):
        """Parse a postdata-style response format from the API into usable data"""

        """Split a a=1b=2c=3 string into a dictionary of pairs"""
        tokens = {r[0]: r[1] for r in [r.split('=') for r in response.split("&")]}

        # The odd dummy parameter is of no use to us
        if 'dummy' in tokens:
            del tokens['dummy']

        """
        If we have key names that end in digits, these indicate the result set contains multiple sets
        For example, planet0=Hoth&x=1&y=-10&planet1=Naboo&x=9&y=13 is actually data for two planets

        Elements that end in digits (like tag0, tag1 for planets) are formatted like (tag0_1, tag1_1), so we rstrip
        underscores afterwards.
        """
        if re.match('\D\d+$', tokens.keys()[0]):
            # Produce a list of dictionaries
            set_tokens = []
            for key, value in tokens:
                key = re.match('^(.+\D)(\d+)$', key)
                # If the key isn't in the format (i.e. a failsafe), skip it
                if key is not None:
                    if key.group(1) not in set_tokens:
                        set_tokens[key.group(1)] = {}

                    set_tokens[key.group(1)][key.group(0).rstrip('_')] = value
            tokens = set_tokens

        return tokens


def get_all_alliance_planets(hapi, tag):
    start = 0
    planets = []

    res = hapi.alliance_planets(tag, start)
    while res.length > 0:
        planets = planets + res
        start += res.length
        res = hapi.alliance_planets(tag, start)

    return planets
