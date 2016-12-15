"""Defines the clock event processor for tracking historical job load."""
from job.clock import ClockEventProcessor
from queue.models import JobLoad


class JobLoadProcessor(ClockEventProcessor):
    """This class queries and stores job load statistics for tracking and trending."""

    def process_event(self, event, last_event=None):
        """See :meth:`job.clock.ClockEventProcessor.process_event`.

        Calculates metrics for the job load over time.
        """
        JobLoad.objects.calculate()
