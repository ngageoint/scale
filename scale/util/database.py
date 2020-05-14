"""Helper methods for os operations"""
import time
from django.db.models.functions import Lower

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


def alphabetize(order, fields):
    """Returns the correct sort order

    :param order: The list of ordering
    :type order: list
    :param fields: The list of fields to alphabetize
    :type fields: list
    """

    ordering = []
    for o in order:
        if o in fields:
            # Check for descending first (prepended with a -)
            if o[0] == '-':
                ordering.append(Lower(o[1:]).desc())
            else:
                ordering.append(Lower(o))
        else:
            ordering.append(o)

    return ordering
