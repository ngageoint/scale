from job.configuration.interface.job_interface import JobInterface
from job.seed.manifest import SeedManifest


class JobInterfaceSunset(object):
    @staticmethod
    def create(interface, do_validate=True):
        if 'seedVersion' in interface:
            return SeedManifest(interface, do_validate=do_validate)
        else:
            return JobInterface(interface, do_validate=do_validate)

