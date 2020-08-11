This is far from complete, give me a bit to finish it. If there are specific API Endpoints you want to access submit an issue and I should be able to implement in a day. 

Until it is complete and packaged for pip this is meant for use as a git submodule/directory inside your project

Installation/First Run:

Auth:

You will have to auth with kaseya on first run. To do this copy sample_config.ini to config.ini and fill it. 

When you launch VSA_Auth.py it will email a link to you, click the link and authorize access. It will redirect you to localhost, copy the entire resulting URL into an email reply and reply to the initial email. Do not include a greeting or signature.

Notes:
Where you see the params var you can use the parameters here: <http://help-origin.kaseya.com/webhelp/EN/RESTAPI/9040000/#31622.htm>

If I wanted to use their first example in python I would do this:

    import PythonVSA as vsa
    
    vsa.AgentProcedures.List("$skip=30&$top=10&$orderby=Severity")

Then PythonVSA would make a request similar to:

    GET /automation/agentprocs?$skip=30&$top=10&$orderby=Severity

Implemented

-------------
Authentication

Agent Procedures:

- List
- Run Now

Agents:

- Find
- GetAllAlarms
- CloseAlarm

Service Desk:

- GetTickets
- GetDesks
- GetTicketCategories
- GetCustomFields
- GetPriorities
- GetCustomFields
- GetTicket
- GetTicketCustomField
- UpdateCustomField
- GetTicketNotes
- AddTicketNote
- UpdateTicketPriority
- UpdateTicketStatus
