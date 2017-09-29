from job.configuration.interface.job_interface import JobInterface
from job.seed.seed_interface import SeedJobInterface


class JobInterfaceSunset(object):
    @staticmethod
    def create(interface):
        if 'seedVersion' in interface:
            return SeedJobInterface(interface)
        else:
            return JobInterface(interface)

