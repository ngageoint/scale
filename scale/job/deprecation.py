from job.configuration.data.job_connection import JobConnection
from job.configuration.interface.job_interface import JobInterface
from job.data.job_connection import SeedJobConnection
from job.seed.manifest import SeedManifest


class JobInterfaceSunset(object):
    """Class responsible for providing backward compatability support for old style JobType interfaces as well as new
    Seed compliant interfaces.

    """
    @staticmethod
    def create(interface_dict, do_validate=True):
        """Instantiate an instance of the JobInterface based on inferred type

        :param interface_dict: deserialized JSON interface
        :type interface_dict: dict
        :param do_validate: whether schema validation should be applied
        :type do_validate: bool
        :return: instance of the job interface appropriate for input data
        :rtype: :class:`job.configuration.interface.job_interface.JobInterface` or :class:`job.seed.manifest.SeedManifest`
        """
        if JobInterfaceSunset.is_seed(interface_dict):
            return SeedManifest(interface_dict, do_validate=do_validate)
        else:
            return JobInterface(interface_dict, do_validate=do_validate)

    @staticmethod
    def is_seed(interface_dict):
        """Determines whether a given interface dict is Seed

        :param interface_dict: deserialized JSON interface
        :type interface_dict: dict
        :return: whether interface is Seed compliant or not
        :rtype: bool
        """
        return 'seedVersion' in interface_dict


class JobConnectionSunset(object):
    """Class responsible for providing backward compatibility for old JobConnection interfaces as well as new Seed
    compliant connections.
    """

    @staticmethod
    def create(interface):
        """Instantiate an appropriately typed Job connection based on interface type

        """

        if isinstance(interface, SeedManifest):
            return SeedJobConnection()
        else:
            return JobConnection()