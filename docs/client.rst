Client
------
.. currentmodule:: cpqpython

.. autoclass:: Client

   .. automethod:: request(self, method, path, data=None, **kwargs)

   .. automethod:: login(self, username, password)

   .. automethod:: logout(self)

   .. automethod:: get_printable_proposal(self, proposal_id, item_id=None, associated_id=None)
