"""Defines the class that keeps track of GPU resources on a per node basis"""
import logging

logger = logging.getLogger(__name__)

class GPUManager(object):
    """The class that holds the GPU library and manages it"""
    __GPUs = {}

    @classmethod
    def assign_gpus_for_job(cls, node_id, job_id, required_gpu_count):
        """
        method that assigns a specific GPU to a job id
        :param node_id: the node ID
        :param job_id: the job ID
        :param required_gpu_count: required GPUs
        """
        logger.info("assigning GPUs, request came for node %s and job %s for %s GPUs", node_id, job_id, required_gpu_count)
        assigned_gpu_count = 0
        assignment_complete = False
        for gpunum, gpustatus in cls.__GPUs[node_id].iteritems():
            logger.info("entered loop looking for gpus to set, expecting to set %s GPUs", int(required_gpu_count))
            if gpustatus == "reserved":
                cls.__GPUs[node_id][gpunum] = job_id
                logger.info("assigned %s to %s", gpunum, job_id)
                assigned_gpu_count += 1
            if assigned_gpu_count == int(required_gpu_count):
                assignment_complete = True
                break # assigned everything we need, exit loop
        if assignment_complete:
            return True
        else:
            return False #TODO revert assigned GPUs, try again?

    @classmethod
    def reserve_gpus_for_job(cls, node_id, required_gpu_count):
        """
        Method that reserves GPUs for future assignment to a job id
        :param node_id: the node id
        :param required_gpu_count: requred GPUs
        """
        logger.info("reserving GPUs, request came for node %s and for %s GPUs", node_id, required_gpu_count)
        assigned_gpu_count = 0
        reserve_complete = False
        for gpunum, gpustatus in cls.__GPUs[node_id].iteritems():
            logger.info("entered loop looking for gpus to set")
            if gpustatus == "available":
                cls.__GPUs[node_id][gpunum] = "reserved"
                assigned_gpu_count += 1
                logger.info("Set %s to reserved", gpunum)
            if assigned_gpu_count == int(required_gpu_count):
                reserve_complete = True
                break # assigned everything we need, exit loop
        return reserve_complete
        # if reserve_complete:
        #     return True
        # else:
        #     return False # TODO revert assigned GPUs, try again?

    @classmethod
    def get_nvidia_docker_label(cls, node_id, job_id):
        """
        method that returns a formatted string that is to be used
        as a variable for nvidia-docker which specifies which GPUs will be used
        :param node_id: the node ID
        :param job_id: the job ID
        """
        gpu_list = ""
        for gpunum, gpustatus in cls.__GPUs[node_id].iteritems():
            if gpustatus == job_id:
                gpu_list += str(gpunum) + ","
        logger.info("final gpu string is %s", gpu_list.strip(','))

        return gpu_list.strip(',')

    @classmethod
    def define_node_gpus(cls, node_id, gpu_count):
        """
        Method that will create new GPUs in the dictionary based on offered resources from MESOS/DCOS
        :param node_id: the node ID
        :param gpu_count: required GPUs
        """
        logger.debug("this node has atleast %s gpu", gpu_count)
        if not node_id in cls.__GPUs: # is this node already in the dict?
            logger.info("node %s did not find itsself in the gpu dic", node_id)
            cls.__GPUs[node_id] = {}
            for i in range(0, int(gpu_count)):
                cls.__GPUs[node_id][i] = "available"
                logger.info("added gpu %s to node %s", i, node_id)
        elif gpu_count > len(cls.__GPUs[node_id]): # a new GPU has been offered from a known node...
            logger.debug("it seems we missed some GPUs... currently have %s accounted for but was offered %s", len(cls.__GPUs[node_id]), gpu_count)
            for i in range(int(len(cls.__GPUs[node_id])), int(gpu_count)):
                cls.__GPUs[node_id][i] = "available"
                logger.info("added gpu %s to %s", i, node_id)
        else: # gpu count is good, node is in the dict... not much to do
            for gpu, key in cls.__GPUs[node_id].iteritems():
                logger.debug("the gpu %s has status %s", gpu, key)
        #TODO add handler for less GPUs than expected to check missing GPUs are listed as unavailable

    @classmethod
    def release_gpus(cls, node_id, job_id):
        """
        Method sets GPU status back to available for completed jobs
            :param node_id: node ID
            :param job_id: job ID
        """
        if node_id in cls.__GPUs:
            for gpunum, gpustatus in cls.__GPUs[node_id].iteritems():
                logger.debug("now in loop checking for GPUs to free. looking at GPU %s with status %s. trying to match to job id %s", gpunum, gpustatus, job_id)
                if str(gpustatus) == str(job_id):
                    cls.__GPUs[node_id][gpunum] = "available"
                    logger.info("job %s is finished, GPU %s set to avilable", job_id, gpunum)

    @classmethod
    def get_gpu_count_for_node(cls, node_id):
        """
        method to retrieve amount of GPUs for a specific node
            :param node_id: node ID
        """   
        return len(cls.__GPUs[node_id])

    @classmethod
    def get_available_gpu_for_node(cls, node_id):
        """
        method to retrieve number of available GPUs for a specific node
            :param node_id: node ID
        """   
        total_available = 0
        for gpunum, gpustatus in cls.__GPUs[node_id].iteritems():
            if gpustatus == "available":
                total_available += 1
        return total_available

    @classmethod
    def reset_gpu_dict(cls):
        """
        resets the GPU dictionary.
        """
        cls.__GPUs = {}
        