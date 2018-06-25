from abc import ABCMeta


class JobDataFields(object):
    __metaclass__ = ABCMeta

    def __init__(self, data):
        self.dict = data

    def __repr__(self):
        return self.dict

    @property
    def name(self):
        return self.dict['name']


class JobDataInputFiles(JobDataFields):
    @property
    def file_ids(self):
        return self.dict['file_ids']


class JobDataInputJson(JobDataFields):
    @property
    def value(self):
        return self.dict['value']


class JobDataOutputFiles(JobDataFields):
    @property
    def workspace_id(self):
        return self.dict['workspace_id']