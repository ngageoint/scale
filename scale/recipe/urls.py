'''Defines the URLs for the RESTful recipe services'''
from django.conf.urls import patterns, url

import recipe.views

urlpatterns = patterns(
    '',

    # Recipe type views
    url(r'^recipe-types/$', recipe.views.RecipeTypesView.as_view(), name='recipe_types_view'),
    url(r'^recipe-types/(\d+)/$', recipe.views.RecipeTypeDetailsView.as_view(), name='recipe_type_details_view'),
    url(r'^recipe-types/validation/$', recipe.views.RecipeTypesValidationView.as_view(),
        name='recipe_types_validation_view'),

    # Recipe views
    url(r'^recipes/$', recipe.views.RecipesView.as_view(), name='recipes_view'),
    url(r'^recipes/(\d+)/$', recipe.views.RecipeDetailsView.as_view(), name='recipe_details_view'),
)
