from job.configuration.interface.job_interface import JobInterface
from job.seed.manifest import SeedManifest


class JobInterfaceSunset(object):
    """Class responsible for providing backward compatability support for old style JobType interfaces as well as new
    Seed compliant interfaces.

    """
    @staticmethod
    def create(interface, do_validate=True):
        """Instantiate an instance of the JobInterface based on inferred type

        :param interface: deserialized JSON interface
        :type interface: type
        :param do_validate: whether schema validation should be applied
        :type do_validate: bool
        :return: instance of the job interface appropriate for input data
        :rtype: :class:`job.configuration.interface.job_interface.JobInterface` or :class:`job.seed.manifest.SeedManifest`
        """
        if JobInterfaceSunset.is_seed(interface):
            return SeedManifest(interface, do_validate=do_validate)
        else:
            return JobInterface(interface, do_validate=do_validate)

    @staticmethod
    def is_seed(interface):
        """Determines whether a given interface dict is Seed

        :param interface: deserialized JSON interface
        :type interface: dict
        :return: whether interface is Seed compliant or not
        :rtype: bool
        """
        return 'seedVersion' in interface

