"""Defines the functions for generating Mesos tasks"""
from __future__ import unicode_literals

import logging
from mesoshttp.offers import Offer
from django.conf import settings


logger = logging.getLogger(__name__)


def create_simple_offer(offer_id):
    """Creates and returns a MesosHTTP useful only for offer combination

    :param offer_id: ID for offer to create
    :type offer_id: int
    :returns: Offer
    :rtype: :class:`mesoshttp.offers.Offer`
    """

    return Offer(None, None, None, {"id":{"value":offer_id}}, None, None)

