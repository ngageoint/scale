from job.configuration.interface.job_interface import JobInterface
from job.seed.manifest import SeedManifest


class JobInterfaceSunset(object):
    @staticmethod
    def create(interface):
        if 'seedVersion' in interface:
            return SeedManifest(interface)
        else:
            return JobInterface(interface)

