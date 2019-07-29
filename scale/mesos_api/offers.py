"""Defines the functions for generating Mesos tasks"""
from __future__ import unicode_literals

import logging

from mesos_api.utils import obj_from_json

logger = logging.getLogger(__name__)


def from_mesos_offer(mesos_offer):
    """Creates a dot accessible offer from input dict

    :param mesos_offer: Offer object to translate into dot accessible object
    :type mesos_offer: :class:`mesoshttp.offers.Offer`
    :returns: Dot accessible object
    :rtype: :class:`Namespace`
    """

    return obj_from_json(mesos_offer.get_offer())