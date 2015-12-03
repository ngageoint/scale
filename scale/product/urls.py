'''Defines the URLs for the RESTful product services'''
from django.conf.urls import patterns, url

import product.views

urlpatterns = patterns(
    '',
    url(r'^products/$', product.views.ProductsView.as_view(), name='products_view'),
    url(r'^products/updates/$', product.views.ProductUpdatesView.as_view(), name='product_updates_view'),
)
