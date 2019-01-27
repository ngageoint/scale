class RecipeHandler(object):
    """This class handles the rules for matching recipe inputs for files processed by Strike and Scans
    """
    
    def __init__(self, recipe_name=None):
        """Constructor
        
        :param recipe_name: The name of the recipe type
        :type recipe_name: string
        """
        self.recipe_name = recipe_name
        self.rules = []
        
    def set_recipe_name(self, name):
        """Sets the recipe name
        
        :param name: Namem of the recipe
        :type name: string
        """
        
        self.recipe_name = name
    
    def add_rule(self, rule):
        """Adds a given rule to the handler
        
        :param rule: The media or data type of the file and input it belongs to
        :type rule: :class:`ingest.handlers.recipe_rule.RecipeRule`
        """
        
        self.rules.append(rule)
        
    def get_rules(self):
        """Returns the rules associated with this recipe handler
        
        :returns: The rules associated with this recipe handler
        :rtype: [:class:`ingest.handlers.recipe_rule.RecipeRule`]
        """
        
        return self.rules
        
    def rule_matches(self, source_file):
        """Checks a given file to determine if it matches and returns the first recipe input that matches
        
        :param source_file: The source file to check
        :type source_file: :class:`source.
        :returns: The rule that matches the source file
        :rtype: :class:`ingest.handlers.RecipeRule`
        """
        
        for rule in self.rules:
            if rule.matches_file(source_file):
                return rule
                