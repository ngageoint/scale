
.. _rest_v6_deprecated:

v6 Deprecated Services
======================

These services were deprecated in v6


/port REST API
--------------
The import/export REST API endpoints were deprecatedin Scale v5 and completely
removed in Scale v6. Replacements are _____

/queue REST API
--------------
Specific endpoints under the queue API were removed in v6.

/queue/new-job/ was moved to the /jobs/ API

/queue/new-recipe/ was moved to the /recipes/ API

/queue/requeue-jobs/ was already deprecated in Scale v5


/source REST API
--------------
The source REST API endpoint was deprecated in Scale v5 and completely removed
in Scale v6. The v6+ replacement for this endpoint is ____

v6 Deprecated Messages
======================

reprocess_recipes Message
-------------------------
This message was deprecated in Scale v6 in favor of the new create_recipes message.

update_recipes Message
----------------------
This message was deprecated in Scale v6 in favor of the update_recipe message.
