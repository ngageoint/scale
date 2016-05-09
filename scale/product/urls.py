"""Defines the URLs for the RESTful product services"""
from django.conf.urls import patterns, url

import product.views as views

urlpatterns = patterns(
    '',
    url(r'^products/$', views.ProductsView.as_view(), name='products_view'),
    url(r'^products/updates/$', views.ProductUpdatesView.as_view(), name='product_updates_view'),
    url(r'^products/(?P<product_id>\d+)/$', views.ProductDetailsView.as_view(), name='product_details_view'),
    url(r'^products/(?P<file_name>[\w.]{0,250})/$', views.ProductDetailsView.as_view(), name='product_details_view'),
)
