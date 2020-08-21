import requests
import datetime
import configparser
from os import getcwd


config = configparser.ConfigParser()
# For use as submodule. Will likely need a change/detection for pip deployment.
fullpath = getcwd() + "\\PythonVSA\\config.ini"
config.read(fullpath, encoding='utf-8')

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
            print("Please delete the [Auth] section of config.ini and reauthenticate with kaseya.")
            # TODO: If refresh_token = line missing just add Auth section with blank refresh_token = 
            # TODO: If reauth needed just delete the section/ignore it and send a new email. Is there a bettter way of handling this?
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
        list : Found agent(s)
        """

        url = api_uri + "/assetmgmt/agents?" + params
        r = requests.get(url=url, headers={
                         "Authorization": "Bearer " + Auth.GetToken(),
                         "Content-Type": "application/json"})
        if(r.status_code == 200):
            data = r.json()['Result']
            return data
        else:
            print("Error in VSA.Agents.Find.")
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
        else:
            print("Error in CloseAlarm.")
            print(r.text)
            return(r.json())

    @classmethod
    def GetCustomFields(cls, agentId):
        """
        Get all custom fields for an agent

        Parameters
        ----------
        agentId : int
            Agent ID to query for custom fields

        Returns
        -------
        dict : Dictionary of custom fields and their values
        """
        url = f"{api_uri}assetmgmt/assets/{str(agentId)}/customfields"
        r = requests.get(url=url, headers={
                         "Authorization": "Bearer " + Auth.GetToken(),
                         "Content-Type": "application/json"})
        print(str(r.status_code))
        if(r.status_code == 200):
            print("GetCustomFields Done")
            return r.json()
        else:
            print("Error in GetCustomFields")
            error = r.json()["Error"]
            if(error == "No custom field exist for specified agent."):
                return 1
            else:
                return error

    @classmethod
    def AddCustomField(cls, FieldName, FieldType):
        """
        Create a new custom field

        Parameters
        ----------
        FieldName : string
            Name of field to create
        FieldType : string
            Type of field, options are: string, number, date time, date, time
        """
        from json import dumps
        url = f"{api_uri}assetmgmt/assets/customfields"
        data = {"FieldName": FieldName, "FieldType": FieldType}

        r = requests.post(url=url, headers={
                         "Authorization": "Bearer " + Auth.GetToken()},
                         data=data)
        if(r.status_code == 200):
            return 200
        else:
            return r.text

    @classmethod
    def UpdateCustomField(cls, agentId, FieldName, FieldValue):
        """
        Update an existing custom field

        Parameters
        ----------
        agentId : int
            GUID of Kaseya agent to update custom field value of
        FieldName : string
            Name of field to update
        FieldValue : string
            Value to insert in chosen field
        """
        url = f"{api_uri}assetmgmt/assets/{agentId}/customfields/{FieldName}"
        data = {"FieldValue": FieldValue}
        r = requests.put(url=url, headers={
                         "Authorization": "Bearer " + Auth.GetToken()},
                         data=data)
        if(r.status_code == 200):
            return 200
        else:
            return r.text


class ServiceDesk:
    """
    http://help-origin.kaseya.com/webhelp/EN/RESTAPI/9040000/#31752.htm
    """
    @classmethod
    def GetTickets(cls, serviceDeskId, params=None):
        """
        Get Tickets based on Service Desk ID
        Parameters
        ----------
        serviceDeskId : int
            ID of service desk to search
        params : string
            Properly formatted string of filters/expressions (see README)
        Returns
        -------
        dict : Tickets Found
        """
        if(params is None):
            url = api_uri + "automation/servicedesks/" + str(serviceDeskId) + "/tickets"
        else:
            url = api_uri + "automation/servicedesks/" + str(serviceDeskId) + "/tickets?" + params
        r = requests.get(url=url, headers={
                         "Authorization": "Bearer " + Auth.GetToken(),
                         "Content-Type": "application/json"})
        if(r.status_code == 200):
            print("Tickets retrieved sucessfully.")
            return r.json()
        else:
            print("Failure in GetTickets.")
            return r.json()

    @classmethod
    def GetDesks(cls, params=None):
        """
        Get all Service Desks
        Parameters
        ----------
        params : string
            Properly formatted string of filters/expressions (see README)
        Returns
        -------
        dict : Service Desks Found
        """
        if(params is None):
            url = api_uri + "automation/servicedesks/"
        else:
            url = api_uri + "automation/servicedesks/" + params
        r = requests.get(url=url, headers={
                         "Authorization": "Bearer " + Auth.GetToken(),
                         "Content-Type": "application/json"})
        if(r.status_code == 200):
            print("Service Desks retrieved sucessfully.")
            return r.json()
        else:
            print("Failure in GetDesks.")
            return r.json()

    @classmethod
    def GetTicketCategories(cls, serviceDeskId, params=None):
        """
        Get Ticket Categories based on Service Desk ID
        Parameters
        ----------
        serviceDeskId : int
            ID of service desk to search
        params : string
            Properly formatted string of filters/expressions (see README)
        Returns
        -------
        dict : Ticket categories
        """
        if(params is None):
            url = api_uri + "automation/servicedesks/" + str(serviceDeskId) + "/categories"
        else:
            url = api_uri + "automation/servicedesks/" + str(serviceDeskId) + "/categories?" + params
        r = requests.get(url=url, headers={
                         "Authorization": "Bearer " + Auth.GetToken(),
                         "Content-Type": "application/json"})
        if(r.status_code == 200):
            print("Ticket categories retrieved sucessfully.")
            return r.json()
        else:
            print("Failure in GetTicketCategories.")
            return r.json()

    @classmethod
    def GetCustomFields(cls, serviceDeskId, params=None):
        """
        Get Custom Fields based on Service Desk ID
        Parameters
        ----------
        serviceDeskId : int
            ID of service desk to search
        params : string
            Properly formatted string of filters/expressions (see README)
        Returns
        -------
        dict : Custom Fields
        """
        if(params is None):
            url = api_uri + "automation/servicedesks/" + str(serviceDeskId) + "/customfields"
        else:
            url = api_uri + "automation/servicedesks/" + str(serviceDeskId) + "/customfields?" + params
        r = requests.get(url=url, headers={
                         "Authorization": "Bearer " + Auth.GetToken(),
                         "Content-Type": "application/json"})
        if(r.status_code == 200):
            print("Custom Fields retrieved sucessfully.")
            return r.json()
        else:
            print("Failure in GetCustomFields.")
            return r.json()

    @classmethod
    def GetPriorities(cls, serviceDeskId, params=None):
        """
        Get Service Desk Priorities based on Service Desk ID
        Parameters
        ----------
        serviceDeskId : int
            ID of service desk to search
        params : string
            Properly formatted string of filters/expressions (see README)
        Returns
        -------
        dict : Service Desk Priorities
        """
        if(params is None):
            url = api_uri + "automation/servicedesks/" + str(serviceDeskId) + "/priorities"
        else:
            url = api_uri + "automation/servicedesks/" + str(serviceDeskId) + "/priorities?" + params
        r = requests.get(url=url, headers={
                         "Authorization": "Bearer " + Auth.GetToken(),
                         "Content-Type": "application/json"})
        if(r.status_code == 200):
            print("Service Desk Priorities retrieved sucessfully.")
            return r.json()
        else:
            print("Failure in GetPriorities.")
            return r.json()

    @classmethod
    def GetTicketStatuses(cls, serviceDeskId, params=None):
        """
        Get Ticket Statuses based on Service Desk ID
        Parameters
        ----------
        serviceDeskId : int
            ID of service desk to search
        params : string
            Properly formatted string of filters/expressions (see README)
        Returns
        -------
        dict : Ticket Statuses
        """
        if(params is None):
            url = api_uri + "automation/servicedesks/" + str(serviceDeskId) + "/status"
        else:
            url = api_uri + "automation/servicedesks/" + str(serviceDeskId) + "/status?" + params
        r = requests.get(url=url, headers={
                         "Authorization": "Bearer " + Auth.GetToken(),
                         "Content-Type": "application/json"})
        if(r.status_code == 200):
            print("Ticket Statuses retrieved sucessfully.")
            return r.json()
        else:
            print("Failure in GetTicketStatuses.")
            return r.json()

    @classmethod
    def GetTicket(cls, ticketId, params=None):
        """
        Get Ticket info based on Ticket ID
        Parameters
        ----------
        ticketId : int
            ID of ticket to retrieve
        params : string
            Properly formatted string of filters/expressions (see README)
        Returns
        -------
        dict : Ticket Information
        """
        if(params is None):
            url = api_uri + "automation/servicedesktickets/" + str(ticketId)
        else:
            url = api_uri + "automation/servicedesktickets/" + str(ticketId) + "?" + params
        r = requests.get(url=url, headers={
                         "Authorization": "Bearer " + Auth.GetToken(),
                         "Content-Type": "application/json"})
        if(r.status_code == 200):
            print("Ticket retrieved sucessfully.")
            return r.json()
        else:
            print("Failure in GetTicket.")
            return r.json()

    @classmethod
    def GetTicketCustomField(cls, ticketId, customFieldId):
        """
        Get Custom Field value
        Parameters
        ----------
        ticketId : int
            ID of ticket to retrieve
        customFieldId : int
            ID of custom field to get value of
        Returns
        -------
        dict : Custom Field Value
        """
        url = api_uri + "automation/servicedesktickets/" + str(ticketId) + "/customfields/" + str(customFieldId)
        r = requests.get(url=url, headers={
                         "Authorization": "Bearer " + Auth.GetToken(),
                         "Content-Type": "application/json"})
        if(r.status_code == 200):
            print("Custom Field Value retrieved sucessfully.")
            return r.json()
        else:
            print("Failure in GetTicketCustomField.")
            return r.json()

    @classmethod
    def UpdateCustomField(cls, ticketId, customFieldId, data):
        """
        Update Custom Field value
        Parameters
        ----------
        ticketId : int
            ID of ticket to retrieve
        customFieldId : int
            ID of custom field to update
        data : string 
            String encapsulated in escaped double quotes to fill custom field
        Returns
        -------
        int : 0 if success | dict with more information on failure
        """
        url = api_uri + "automation/servicedesktickets/" + str(ticketId) + "/customfields/" + str(customFieldId)
        r = requests.put(url=url, headers={
                         "Authorization": "Bearer " + Auth.GetToken(),
                         "Content-Type": "application/json"},
                         data=data)
        if(r.status_code == 200):
            print("Custom Field Updated.")
            return 0
        else:
            print("Failure in UpdateCustomField.")
            return r.json()

    @classmethod
    def GetTicketNotes(cls, ticketId, params=None):
        """
        Get Ticket notes based on Ticket ID
        Parameters
        ----------
        ticketId : int
            ID of ticket to retrieve
        params : string
            Properly formatted string of filters/expressions (see README)
        Returns
        -------
        dict : Ticket Notes
        """
        if(params is None):
            url = api_uri + "automation/servicedesktickets/" + str(ticketId) + "/notes"
        else:
            url = api_uri + "automation/servicedesktickets/" + str(ticketId) + "/notes?" + params
        r = requests.get(url=url, headers={
                         "Authorization": "Bearer " + Auth.GetToken(),
                         "Content-Type": "application/json"})
        if(r.status_code == 200):
            print("Ticket Notes retrieved sucessfully.")
            return r.json()
        else:
            print("Failure in GetTicketNotes.")
            return r.json()

    @classmethod
    def AddTicketNote(cls, ticketId, note, hidden="true", systemflag="true"):
        """
        Add note to ticket
        Parameters
        ----------
        ticketId : int
            ID of ticket to add note against
        note : string
            Note to add to ticket
        Returns
        -------
        int : 0 if success | dict with more information on failure
        """
        url = api_uri + "automation/servicedesktickets/" + str(ticketId) + "/notes"
        data = {"Hidden": hidden,
                "SystemFlag": systemflag,
                "Text": note}
        r = requests.post(url=url, headers={
                         "Authorization": "Bearer " + Auth.GetToken(),
                         "Content-Type": "application/json"}, data=data)
        if(r.status_code == 200):
            print("Ticket Note Added successfully.")
            return 0
        else:
            print("Failure in AddTicketNote.")
            return r.json()

    @classmethod
    def UpdateTicketPriority(cls, ticketId, priorityId):
        """
        Update Ticket Priority
        Parameters
        ----------
        ticketId : int
            ID of ticket to change priority of
        priorityId : int
            Priority to set
        Returns
        -------
        int : 0 if success | dict with more information on failure
        """
        url = api_uri + "automation/servicedesktickets/" + str(ticketId) + "/priority/" + str(priorityId)
        r = requests.put(url=url, headers={
                         "Authorization": "Bearer " + Auth.GetToken(),
                         "Content-Type": "application/json"})
        if(r.status_code == 200):
            print("Ticket Priority Updated successfully.")
            return 0
        else:
            print("Failure in UpdateTicketPriority.")
            return r.json()

    @classmethod
    def UpdateTicketStatus(cls, ticketId, statusId):
        """
        Update Ticket Status
        Parameters
        ----------
        ticketId : int
            ID of ticket to change status of
        statusId : int
            Status to set
        Returns
        -------
        int : 0 if success | dict with more information on failure
        """
        url = api_uri + "automation/servicedesktickets/" + str(ticketId) + "/status/" + str(statusId)
        r = requests.put(url=url, headers={
                         "Authorization": "Bearer " + Auth.GetToken(),
                         "Content-Type": "application/json"})
        if(r.status_code == 200):
            print("Ticket Status Updated successfully.")
            return 0
        else:
            print("Failure in UpdateTicketStatus.")
            return r.json()
