import requests
import json
import sys
import logging
# NOTE All logs are at level error for convinience until we have time to setup logging
# appropriately
logger = logging.getLogger(__name__)


# TODO This looks really dumb, Sorry Darwin :), we should replace with loggin
def _paranoid_print(msg):
    try:
        print >> sys.stderr, msg
    except:
        print >> sys.stderr, "Couldn't print the message; it's probably an encoding error of some sort."


class Client(object):
    """The CPQ Rest API Client.

    :param server_name: The location of the server
    :type server_name: str
    :param version: The CPQ API version
    :type version: str
    :param username: The username for the user
    :type username: str
    :param password: The password for the user
    :type password: str

    If username and password are present, we automatically call :func:`login`.

    >>> client = Client()
    >>> client = Client(username="user@name.com", password="password")
    """
    server_name = None
    version = None
    base_path = None
    session_id = None

    def __init__(
        self, server_name=None, version="15",
        username=None, password=None,
        debug=False, gliderapikey=None
    ):
        self.server_name = server_name
        self.version = version
        self.base_path = "/rs/{0}".format(version)
        self.debug = debug
        self.gliderapikey = gliderapikey
        if username and password:
            self.login(username, password)
        elif username and gliderapikey:
            self.login(username, gliderapikey=gliderapikey)

    def request(self, method, path, data=None, **kwargs):
        """The base request builder.

        :param method: The HTTP method type
        :type method: str
        :param path: The path to the resource
        :type path: str
        :param data: The data to pass to the request
        :type data: dict
        """
        url = "{0}{1}{2}".format(self.server_name, self.base_path, path)
        headers = kwargs.pop('headers', {})
        cookies = kwargs.pop('cookies', {})
        headers.update({"content-type": "application/json"})
        if self.session_id:
            cookies['JSESSIONID'] = self.session_id
        if self.debug:
            _paranoid_print("Request:")
            _paranoid_print(method + ' ' + url)
            _paranoid_print("Headers:")
            for headerkey in headers.keys():
                _paranoid_print(headerkey + ': ' + headers[headerkey])
            _paranoid_print("Cookies:")
            for cookiekey in cookies.keys():
                _paranoid_print(cookiekey + ': ' + cookies[cookiekey])
        response = requests.request(
            method, url, data=json.dumps(data), headers=headers,
            cookies=cookies, **kwargs
        )
        if self.debug:
            _paranoid_print("Response:")
            _paranoid_print(str(response.status_code) + ' ' + response.reason)
            _paranoid_print("Headers:")
            for headerkey in headers.keys():
                _paranoid_print(headerkey + ': ' + headers[headerkey])
            _paranoid_print("Body:")
            _paranoid_print(response.text)
        return response

    def login(self, username, password=None, gliderapikey=None):
        """Log the user into CPQ.

        :param username: The username of the user
        :type username: str
        :param password: The password of the user
        :type password: str
        :returns: requests.models.Response
        :param gliderapikey: The Glider ApiKey
        :type gliderapikey: str

        >>> client.login("user@name.com", "password")
        >>> client.login("user@name.com", gliderapikey="1234")
        """
        data = {"username": username}
        if gliderapikey:
            data["gliderapikey"] = gliderapikey
        else:
            data["password"] = password
        resp = self.request("POST", "/cpq/login", data)
        if resp.status_code == 200:
            # Get the JSESSIONID for later requests
            self.session_id = resp.cookies.get("JSESSIONID", None)
        return resp

    def logout(self):
        """Log the user out of CPQ."""
        return self.request("POST", "/cpq/logout")

    def get_printable_proposal(self, proposal_id, item_id=None, associated_id=None):
        """Retreive a printable proposal.

        :param proposal_id: The ID of the proposal
        :type proposal_id: str
        :param item_id: The ID of a ProposalReport
        :type item_id: str
        :param associated_id: The ID for a Opportunity, Quote or ConfiguredProduct object.
        :type associated_id: str

        >>> client.get_printable_proposal("10a000012a6ijitj")
        >>> client.get_printable_proposal("10a000012a6ijitj", item_id="item")
        >>> client.get_printable_proposal("10a000012a6ijitj", associated_id="assoc")
        """
        logger.error('get_printable_proposal')
        params = {}
        if item_id:
            params['itemId'] = item_id
        if associated_id:
            params['associatedId'] = associated_id
        path = "/cpqproposal/{0}/printable".format(proposal_id)
        logger.error('path: {}'.format(path))
        logger.error('params: {}'.format(params))
        response = self.request("GET", path, params=params)

        if response.status_code != 200:
            logger.error('Problem with getting the proposal, status code: {}'.format(
                response.status_code))
            logger.error('Response content on next line:\n{}'.format(response.content))

        return response

    def query(self, query, batchsize=200):
        """Perform a query on the CPQ Api.

        :param query: The query to call on the CPQ API
        :type query: str

        >>> client.query("Select ShippingCity from Account")
        """
        return self.request(
            "GET", "/cpq", params={'query': query, 'batchsize': batchsize}
        )

    def update(self, object_id, data=None):
        """Update a CPQ object."""
        if not data:
            data = {}
        return self.request(
            "PUT", "/cpq/{0}".format(object_id), data
        )

    def get_primary_contact(self, proposal_id, useExportUser=False):
        return self.request(
            "GET", "/cpqproposal/{0}/primarycontact".format(
                proposal_id
            ), {
                'useExportUser': useExportUser
            }
        )

    def get_opportunity_external_id(self, opportunity_id):
        res = self.query("Select ExternalId From Opportunity Where Id='{0}'".format(opportunity_id))
        try:
            res_json = res.json()
            return res_json['records'][0].get('ExternalId', None)
        except:
            return None

    def export_to_cpq_app(self, app_url=None, data=None):
        """ Used for exporting data to a cpq/sfdc app extension, which
            will be a different url than a typical cpq api request
        """
        headers = {'content-type': 'application/json'}

        # Set query string parameters for authentication
        app_ext_path = '/ws/14/'

        # NOTE: (darwinhang) We were originally using a dict for the params,
        # which makes for cleaner code, but 'requests' automatically uriencodes
        # the params. This is a problem when working with the cpq sfdc app
        # extensions, because the app extensions are also encoding the url.
        # Since it is much easier for us to make code changes, we are now
        # passing in a string, which won't be uriencoded.
        jsessionid = self.session_id
        cpq_app_url = ''.join([self.server_name.rstrip('/'), app_ext_path])
        querystring = 'appext.cpq.session={jsessionid}&appext.cpq.url={cpq_app_url}'

        if not data:
            data = {}
        return requests.post(
            app_url,
            params=querystring.format(jsessionid=jsessionid, cpq_app_url=cpq_app_url),
            headers=headers,
            data=json.dumps(data)
        )
