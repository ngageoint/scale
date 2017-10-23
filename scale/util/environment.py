def normalize_env_var_name(name):
    """Returns a normalized version of the given string name so it can be used as the name of an environment variable

    :param name: The string name to normalize
    :type name: string
    :returns: The normalized environment variable name
    :rtype: string
    """

    return name.replace('-', '_').upper()