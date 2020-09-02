class VSAError(Exception):
    """Generic error returned from VSA"""
    def __init__(self, *args):
        import inspect
        print("------------------ Begin details ------------------")
        print(f"A generic error occurred in {inspect.stack()[1].function}.")
        print("If more details are available they will be printed below:")
        if args:
            print(f"{args[0]}")
        print("------------------ End details ------------------")

# TODO: Remove these if we can't use them anywhere
#class AgentNotFound(VSAError):
#    """The specified agent could not be found in Kaseya"""
#    def __init__(self, AgentID, RequestObject):
#        print(f"The AgentId {AgentID} was not found in VSA. Please check the ID.")
#        print(f"We tried to contact this url: {print('Requested URL goes here.')}")


#class TicketNotFound(VSAError):
#    """We were unable to find the requested ticket."""
#    def __init__(self, TicketID, RequestObject):
#        print(f"The Ticket with ID/Reference {TicketID} was not found in VSA. Please check the ID/Reference.")
#        print(f"We tried to contact this url: {print('Requested URL goes here.')}")


class ItemNotFound(VSAError):
    """We were either unable to find the requested ticket or status."""
    def __init__(self, RequestObject):
        print("------------------ Begin details ------------------")
        print("An ID/Reference in the request was not found in Kaseya.")
        print(f"We tried to contact this url: {RequestObject.url}")
        print(f"Raw response from Kaseya:\n {RequestObject.text}")
        print("------------------ End details ------------------")
