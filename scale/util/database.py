"""Helper methods for os operations"""
import time

MAX_SLEEP_MS = 500

def sleep(the_model, the_id):
    """Sleeps for a maximum of 5 seconds while waiting for an object to become available
    :param the_class: The model we're trying to find
    :type the_model: Class
    :param the_id: The id of the object we're trying to find
    :type the_id: int
    """
    
    # wait max of 5 seconds for events to save
    tries = 0
    while tries < MAX_SLEEP_MS:
        time.sleep(.01)
        tries += 1
        try:
            the_result = the_model.objects.get(id=the_id)
            if the_result:
                return True
        except the_model.DoesNotExist:
            pass
        
    return False
 