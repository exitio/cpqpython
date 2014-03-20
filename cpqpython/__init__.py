import requests
import json

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
    """
    server_name = None
    version = None
    base_path = None
    session_id = None

    def __init__(
        self, server_name="http://cobalt.fpx.com:8080", version="7",
        username=None, password=None
    ):
        self.server_name = server_name
        self.version = version
        self.base_path = "/rs/{0}".format(version)
        if username and password:
            self.login(username, password)

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
        return requests.request(
            method, url, data=json.dumps(data), headers=headers,
            cookies=cookies, **kwargs
        )

    def login(self, username, password):
        """Log the user into CPQ.

        :param username: The username of the user
        :type username: str
        :param password: The password of the user
        :type password: str
        :returns: requests.models.Response

        >>> client.login("user@name.com", "password")
        """
        resp = self.request("POST", "/cpq/login", {
            "username": username,
            "password": password
        })
        if resp.status_code == 200:
            # Get the JSESSIONID for later requests
            self.session_id = resp.cookies.get("JSESSIONID", None)
        return resp

    def logout(self):
        """Log the user out of CPQ."""
        return self.request("POST", "/cpq/logout")

    def get_printable_proposal(
        self, proposal_id, item_id=None, associated_id=None
    ):
        """Retreive a printable proposal.

        :param proposal_id: The ID of the proposal
        :type proposal_id: str
        :param item_id: The ID of a ProposalReport
        :type item_id: str
        :param associated_id: The ID for a Opportunity, Quote or ConfiguredProduct object.
        :type associated_id: str

        >>> client.get_printable_proposal("proposal")
        >>> client.get_printable_proposal("proposal", item_id="item")
        >>> client.get_printable_proposal("proposal", associated_id="assoc")
        """
        params = {}
        if item_id:
            params['itemId'] = item_id
        if associated_id:
            params['associatedId'] = associated_id
        return self.request(
            "GET",
            "/cpqproposal/{0}/printable".format(proposal_id),
            params=params
        )
