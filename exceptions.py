class VSAError(Exception):
    """Generic error returned from VSA"""
    def __init__(self, *args):
        import inspect
        print("------------------ Begin VSAError ------------------")
        print(f"A generic error occurred in {inspect.stack()[1].function}.")
        print("If more details are available they will be printed below:")
        if args:
            print(f"{args[0]}")
        print("------------------ End VSAError ------------------")


class ItemNotFound(VSAError):
    """We were unable to find the requested ticket or status."""
    def __init__(self, RequestObject):
        print("------------------ Begin ItemNotFound ------------------")
        print("An ID/Reference in the request was not found in Kaseya.")
        print(f"We tried to contact this url: {RequestObject.url}")
        print(f"Raw response from Kaseya:\n {RequestObject.text}")
        print("------------------ End ItemNotFound ------------------")

class AuthError(Exception):
    """The authentication with VSA is broken."""
    def __init__(self, *args):
        print("Got error 403 forbidden. The authentication either broke or you aren't authorized to perform the action you are attempting.")
        exit()