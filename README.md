Yesmail Tools
=============

A set of tools to help with Yesmail development.

Email development workflow usually involves: updating the remote Master template and testing it with remotely triggered code/variables.
These command line tools make it really easy to upload asset changes, clean up the remote master and most importantly preseve changes in local git repo.

##ymbot:##
	Git backed versioning tool with support to upload/download/cleanup assets.
	Add base64 authorization header to a new file http_auth_token and place it in the same folder as ymbot

