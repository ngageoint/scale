"""Defines the URLs for the RESTful recipe services"""
from django.conf.urls import url

import recipe.views

urlpatterns = [
    # Recipe type views
    url(r'^recipe-types/$', recipe.views.RecipeTypesView.as_view(), name='recipe_types_view'),
    # TODO: Remove RecipeTypeIDDetailsView url entry when V5 API is removed
    url(r'^recipe-types/validation/$', recipe.views.RecipeTypesValidationView.as_view(),
        name='recipe_types_validation_view'),
    url(r'^recipe-types/(?P<name>[\w.-]+)/$', recipe.views.RecipeTypeDetailsView.as_view(), name='recipe_type_details_view'),
    url(r'^recipe-types/(?P<name>[\w.-]+)/revisions/$', recipe.views.RecipeTypeRevisionsView.as_view(), name='recipe_type_revisions_view'),
    url(r'^recipe-types/(?P<name>[\w.-]+)/revisions/(?P<revision_num>\d+)/$', recipe.views.RecipeTypeRevisionDetailsView.as_view(), name='recipe_type_revision_details_view'),


    # Recipe views
    url(r'^recipes/$', recipe.views.RecipesView.as_view(), name='recipes_view'),
    url(r'^recipes/(\d+)/$', recipe.views.RecipeDetailsView.as_view(), name='recipe_details_view'),
    url(r'^recipes/(\d+)/input_files/$', recipe.views.RecipeInputFilesView.as_view(), name='recipe_input_files_view'),
    url(r'^recipes/(\d+)/reprocess/$', recipe.views.RecipeReprocessView.as_view(), name='recipe_reprocess_view'),
]
