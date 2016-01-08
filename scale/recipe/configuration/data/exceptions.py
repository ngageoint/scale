'''Defines exceptions that can occur when interacting with recipe data'''


class InvalidRecipeConnection(Exception):
    '''Exception indicating that the provided recipe connection was invalid
    '''

    pass


class InvalidRecipeData(Exception):
    '''Exception indicating that the provided recipe data was invalid
    '''

    pass
