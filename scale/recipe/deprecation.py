from recipe.configuration.data.recipe_data import RecipeData as RecipeData_1_0
from recipe.configuration.definition.recipe_definition_1_0 import RecipeDefinition as RecipeDefinition_1_0
from recipe.seed.recipe_data import RecipeData
from recipe.seed.recipe_definition import RecipeDefinition


class RecipeDefinitionSunset(object):
    """Class responsible for providing backward compatibility support for old style RecipeDefinition interfaces as well
    as new Seed compliant interfaces.

    """
    @staticmethod
    def create(definition_dict):
        """Instantiate an instance of the JobInterface based on inferred type

        :param definition_dict: deserialized JSON definition
        :type definition_dict: dict
        :return: instance of the RecipeDefinition appropriate for input data
        :rtype: :class:`recipe.configuration.definition.recipe_definition_1_0.RecipeDefinition`
                or :class:`recipe.seed.recipe_definition.RecipeDefinition`
        """
        if RecipeDefinitionSunset.is_seed_dict(definition_dict):
            return RecipeDefinition(definition_dict)
        else:
            return RecipeDefinition_1_0(definition_dict)

    @staticmethod
    def is_seed_dict(definition_dict):
        """Determines whether a given definition dict is Seed compatible

        :param definition_dict: deserialized JSON definition
        :type definition_dict: dict
        :return: whether definition is Seed compatible or not
        :rtype: bool
        """
        return definition_dict.get('version', '1.0') != '1.0'

    @staticmethod
    def is_seed(definition):
        """Determines whether a given definition is Seed compatible

        :param definition: instance of Recipe definition
        :type definition_dict: :class:`recipe.configuration.definition.recipe_definition_1_0.RecipeDefinition` or
                               :class:`recipe.seed.recipe_definition.RecipeDefinition`
        :return: whether definition is Seed compatible or not
        :rtype: bool
        """
        return isinstance(definition, RecipeDefinition)


class RecipeDataSunset(object):
    """Class responsible for providing backward compatibility for old RecipeData interfaces as well as new Seed
    compliant ones.
    """

    @staticmethod
    def create(definition, data=None):
        """Instantiate an appropriately typed RecipeData based on definition"""

        if RecipeDefinitionSunset.is_seed(definition):
            return RecipeData(data)
        else:
            return RecipeData_1_0(data)