yesmail_tools
=============

A set of tools to help with Yesmail development.

Email development workflow usually involves: updating the remote Master template and testing it with remotely triggered code/variables.
These command line tools make it really easy to upload asset changes, clean up the remote master and most importantly preseve changes in local git repo.

##ymbot:##
	Allows pushing and fetching assets to and from yesmail.
	Add a new file http_auth_token with the HTTP authorization base64 token in the same folder.
	Automatically adds assets to git

