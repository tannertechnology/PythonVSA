import VSA_Auth
import requests
import datetime
import configparser


config = configparser.ConfigParser()
config.read('config.ini')
vsa_uri = config['VSA']['vsa_uri']
api_uri = vsa_uri + "/api/v1.0/"
redirect_uri = config['Listener']['redirect_uri']
client_id = config['VSA']['client_id']
client_secret = config['VSA']['client_secret']


class Auth:
    @classmethod
    def doRefresh(cls, refresh_token=config['Auth']['refresh_token']):
        config.read('config.ini')
        refreshuri = vsa_uri + "/api/v1.0/token"
        print("Refreshing token...")
        r = requests.post(refreshuri, json={
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                        "redirect_uri": redirect_uri,
                        "client_id": client_id,
                        "client_secret": client_secret})
        if(r.status_code == 400):
            # Email error here. 
            print("Please delete the [Auth] section of config.ini and reauthenticate with kaseya.")
            print(r.text)
            exit()
        else:
            config['Auth']['refreshed_at'] = datetime.datetime.now().strftime("%Y%m%d%H%M")
            config['Auth']['refresh_token'] = r.json()['refresh_token']
            config['Auth']['access_token'] = r.json()['access_token']
            with open('config.ini', 'w') as configfile:
                config.write(configfile)
            print(r.text)
            return r.json()['access_token']

    @classmethod
    def GetToken(cls):
        config.read('config.ini')
        try:
            refresh_token = config['Auth']['refresh_token']
            refreshed_at = config['Auth']['refreshed_at']
            access_token = config['Auth']['access_token']
        except(KeyError):
            print("You haven't properly initialized this library.")
            print("Please run VSA_API.py or Auth.py to perform initial setup.")
            exit()
        refreshdelta = int(datetime.datetime.now().strftime("%Y%m%d%H%M")) - int(refreshed_at)
        if(refreshdelta >= 20):
            print("Refreshing token.")
            access_token = Auth.doRefresh(refresh_token)
        else:
            print("No need to refresh.")

        return access_token



class AgentProcedures:
    """http://help-origin.kaseya.com/webhelp/EN/RESTAPI/9040000/#31639.htm"""
    @classmethod
    def List(cls, params=None):
        """
        Get list of Agent Procedures

        http://help-origin.kaseya.com/webhelp/EN/RESTAPI/9040000/#31641.htm

        Parameters
        ----------
        params : str
            Extra request parameters (http://help-origin.kaseya.com/webhelp/EN/RESTAPI/9040000/#31622.htm)
        
        Returns
        -------
        dict : JSON Dictionary of Agent Procedures
        """
        if(params is None):
            url = api_uri + "automation/agentprocs"
        else:
            url = api_uri + "automation/agentprocs?" + params
        r = requests.get(url=url, headers={
                         "Authorization": "Bearer " + Auth.GetToken(),
                         "Content-Type": "application/json"})
        print(r.text)
        return r.json()

    @classmethod
    def RunNow(cls, agentId, procedureId, params=None):
        """
        Run an Agent Procedure ASAP

        http://help.kaseya.com/webhelp/EN/restapi/9050000/#31668.htm

        Parameters
        ----------
        agentId : int
            ID of agent to execute procedure on
        procedureId : int
            ID of agent procedure to execute

        Returns
        -------
        int : 0 on success | Dictionary with more information on failure
        """
        url = api_uri + "automation/agentprocs/" + str(agentId) + "/" + str(procedureId) + "/runnow"
        r = requests.put(url=url, headers={
                         "Authorization": "Bearer " + Auth.GetToken(),
                         "Content-Type": "application/json"})
        print(r.text)
        if(r.status_code == 204):
            print("VSA.AgentProcedures.RunNow Successful.")
            return 0
        else:
            print("VSA.AgentProcedures.RunNow failed.")
            return r.json()
        

class Agents:
    """http://help.kaseya.com/webhelp/EN/restapi/9050000/#31621.htm"""
    @classmethod
    def Find(cls, params):
        """
        Find an agentId using a number of parameters

        Parameters
        ----------
        params : string
            Properly formatted string of filters/expressions (see README)
        
        Returns
        -------
        int : The Agent ID of the first result Kaseya returns
        """
        url = api_uri + "/assetmgmt/agents?" + params
        r = requests.get(url=url, headers={
                         "Authorization": "Bearer " + Auth.GetToken(),
                         "Content-Type": "application/json"})
        print(r.text)
        if(r.status_code == 200):
            print("Find Successful.")
            data = r.json()['Result']
            data = data[0]['AgentId']
            return int(data)
        else:
            print("Error in VSA.Agents.Find.")
            print(r.text())
            return r.json()

    @classmethod
    def GetAllAlarms(cls, returnAll="true", params=None):
        """
        Get all alarms

        Parameters
        ----------
        returnAll : string
            "true" or "false". True will always download all open alarms, false will only download the alarms this application hasn't downloaded previously. 
        params : string
            Properly formatted string of filters/expressions (see README)
        
        Returns
        -------
        dict : Dictionary of alarms (http://help.kaseya.com/webhelp/EN/restapi/9050000/#38512.htm)
        """
        if(params is None):
            url = api_uri + "assetmgmt/alarms/" + returnAll
        else:
            url = api_uri + "assetmgmt/alarms/" + returnAll + "?" + params
        r = requests.get(url=url, headers={
                         "Authorization": "Bearer " + Auth.GetToken(),
                         "Content-Type": "application/json"})
        if(r.status_code == 200):
            print("GetAllAlarms Done")
            return r.json()
    
    @classmethod
    def CloseAlarm(cls, alarmId, reason="PythonVSA"):
        """
        Close Alarm

        Parameters
        ----------
        alarmId : int
            Alarm ID
        reason : string
            Reason you are closing the alarm
        
        Returns
        -------
        int : 0 on success | Dictionary with more information on failure
        """
        url = api_uri + "assetmgmt/alarms/" + str(alarmId) + "/close"
        r = requests.put(url=url, headers={
                         "Authorization": "Bearer " + Auth.GetToken(),
                         "Content-Type": "application/json"}, data=[{"key": "notes",
                                                                     "value": reason}])
        if(r.status_code == 200):
            return 0
