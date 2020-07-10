Installation/First Run:

Auth:
You will have to auth with kaseya on first run. Make sure you have a domain or ip pointing at the machine running this library and have opened a port specified in VSA_API.ini as listen_port. Set the redirect_uri to http://yourip:port/ and set the same in Kaseya


Notes:
Where you see the params var you can use the parameters here: http://help-origin.kaseya.com/webhelp/EN/RESTAPI/9040000/#31622.htm

If I wanted to use their first example in python I would do this:

    import VSA
    
    VSA.AgentProcedures.List("$skip=30&$top=10&$orderby=Severity")

Then PythonVSA would make a request similar to:

    GET /automation/agentprocs?$skip=30&$top=10&$orderby=Severity



Create issues for:
- NGINX support
- 


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