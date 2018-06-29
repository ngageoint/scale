from recipe.configuration.data.recipe_connection import LegacyRecipeConnection
from recipe.configuration.data.recipe_data import LegacyRecipeData
from recipe.configuration.definition.recipe_definition import LegacyRecipeDefinition
from recipe.seed.recipe_connection import RecipeConnection
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
        :rtype: :class:`recipe.configuration.definition.recipe_definition_1_0.RecipeDefinition_1_0` or
                :class:`recipe.seed.recipe_definition.RecipeDefinition`
        """
        if RecipeDefinitionSunset.is_seed_dict(definition_dict):
            return RecipeDefinition(definition_dict)
        else:
            return LegacyRecipeDefinition(definition_dict)

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
        :type definition_dict: :class:`recipe.configuration.definition.recipe_definition_1_0.RecipeDefinition_1_0` or
                               :class:`recipe.seed.recipe_definition.RecipeDefinition`
        :return: whether definition is Seed compatible or not
        :rtype: bool
        """
        return isinstance(definition, RecipeDefinition)


class RecipeConnectionSunset(object):
    """Class responsible for providing backward compatibility for old RecipeConnection interfaces as well as new Seed
    compliant connections.
    """

    @staticmethod
    def create(definition):
        """Instantiate an appropriately typed Recipe connection based on interface type

        :param definition: instantiated Recipe definition
        :type definition: :class:`recipe.configuration.definition.recipe_definition_1_0.RecipeDefinition_1_0` or
                          :class:`recipe.seed.recipe_definition.RecipeDefinition`
        :return:
        """

        if RecipeDefinitionSunset.is_seed(definition):
            return RecipeConnection()
        else:
            return LegacyRecipeConnection()

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
            return LegacyRecipeData(data)
