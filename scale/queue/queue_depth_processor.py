'''Defines the QueueDepthProcessor for tracking historical queue depth.'''
from job.clock import ClockEventProcessor
from queue.models import Queue, QueueDepthByJobType, QueueDepthByPriority


# TODO: Remove this once the UI migrates to /load
class QueueDepthProcessor(ClockEventProcessor):
    '''This class queries and stores job queue depth statistics for tracking and trending.'''

    def process_event(self, event, last_event=None):
        '''See :meth:`job.clock.ClockEventProcessor.process_event`.

        Calculates metrics for the queue depth over time.
        '''
        depth_by_job_type, depth_by_priority = Queue.objects.get_current_queue_depth()

        QueueDepthByJobType.objects.save_depths(event.occurred, depth_by_job_type)
        QueueDepthByPriority.objects.save_depths(event.occurred, depth_by_priority)
