Core condoor components
=======================

.. automodule:: condoor

Connection class
----------------

.. autoclass:: Connection

   .. automethod:: __init__
   .. automethod:: connect
   .. automethod:: reconnect
   .. automethod:: disconnect
   .. automethod:: reload
   .. automethod:: send
   .. automethod:: enable
   .. automethod:: run_fsm
   .. automethod:: discovery

   .. autoattribute:: family
   .. autoattribute:: platform
   .. autoattribute:: os_type
   .. autoattribute:: os_version
   .. autoattribute:: hostname
   .. autoattribute:: prompt
   .. autoattribute:: is_connected
   .. autoattribute:: is_discovered
   .. autoattribute:: is_console
   .. autoattribute:: mode
   .. autoattribute:: name
   .. autoattribute:: description
   .. autoattribute:: pid
   .. autoattribute:: vid
   .. autoattribute:: sn
   .. autoattribute:: udi
   .. autoattribute:: device_info
   .. autoattribute:: description_record
