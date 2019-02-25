import threading
import logging

logger = logging.getLogger(__name__)

class GPUManager(object):
    __GPUs = {}
    
    @classmethod
    def assign_gpus_for_job(cls,node_id, job_id, required_gpu_count):
        
        assignedGPUCount = 0
        assignmentComplete = False
        for gpunum, gpustatus in cls.__GPUs[node_id].iteritems():
            logger.info("entered loop looking for gpus to set, expecting to set %s GPUs", int(required_gpu_count))
            if gpustatus == "reserved":
                cls.__GPUs[node_id][gpunum] = job_id
                logger.info("assigned %s to %s", gpunum, job_id)
                assignedGPUCount += 1
            if assignedGPUCount == required_gpu_count:
                assignmentComplete = True
                break # assigned everything we need, exit loop
        if assignmentComplete:
            return True
        else:
            return False #TODO revert assigned GPUs, try again?
        
    @classmethod
    def reserve_gpus_for_job(cls,node_id, required_gpu_count):
        
        assignedGPUCount = 0
        reserveComplete = False
        for gpunum, gpustatus in cls.__GPUs[node_id].iteritems():
            logger.info("entered loop looking for gpus to set")
            if gpustatus == "available":
                cls.__GPUs[node_id][gpunum] = "reserved"
                assignedGPUCount += 1
                logger.info("Set %s to reserved", gpunum)
            if assignedGPUCount == int(required_gpu_count):
                reserveComplete = True 
                break # assigned everything we need, exit loop
        if reserveComplete:
            return True
        else:
            return False # TODO revert assigned GPUs, try again?
    
    @classmethod
    def get_nvidia_docker_label(cls, node_id, job_id):
        
        gpu_list = ""
        for gpunum, gpustatus in cls.__GPUs[node_id].iteritems():
            #logger.info("attempting to match gpu to job id. node id is %s and job_exe.id is %s and job_exe.job_id is %s and job_exe.job_exe_id is %s", job_exe.node_id, job_exe.id, job_exe.job_id, "job_exe.job_exe_id")
            if gpustatus == job_id:
                gpu_list += str(gpunum) + ","

        # for i in range(0,int(resource.value)):
            # gpu_list += str(i) + ","                    
        logger.info("final gpu string is %s", gpu_list.strip(','))

        
        return gpu_list.strip(',')
    
    @classmethod
    def DefineNodeGPUs(cls, node_id, gpu_count):
        
        logger.info("this node has atleast %s gpu", gpu_count)
        if not node_id in cls.__GPUs: # is this node already in the dict?
            logger.info("node %s did not find itsself in the gpu dic", node_id)
            cls.__GPUs[node_id] = {}
            for i in range(0,int(gpu_count)):
                cls.__GPUs[node_id][i]= "available"
                logger.info("added gpu %s to node %s", i, node_id)
        elif gpu_count > len(cls.__GPUs[node_id]) : # a new GPU has been offered from a known node...
            logger.info("it seems we missed some GPUs... currently have %s accounted for but was offered %s",len(cls.__GPUs[node_id]),gpu_count)
            for i in range(int(len(cls.__GPUs[node_id])),int(gpu_count)):
                cls.__GPUs[node_id][i]= "available"
                logger.info("added gpu %s to %s",i,node_id)
        else: # gpu count is good, node is in the dict... not much to do
            for GPU, KEY in cls.__GPUs[node_id].iteritems():
                logger.info("the gpu %s has status %s", GPU, KEY)
        #TODO add handler for less GPUs than expected to check missing GPUs are listed as unavailable
    
    @classmethod
    def releaseGPUs(cls, node_id, job_id):
        
        if node_id in cls.__GPUs:
            for gpunum, gpustatus in cls.__GPUs[node_id].iteritems():
                logger.info("now in loop checking for GPUs to free. looking at GPU %s with status %s. trying to match to job id %s",gpunum, gpustatus, job_id)
                if str(gpustatus) == str(job_id):
                    cls.__GPUs[node_id][gpunum] = "available"
                    logger.info("job %s is finished, GPU %s set to avilable",job_id,gpunum)

    @classmethod
    def get_gpu_count_for_node(cls, node_id):
        
        return len(cls.__GPUs[node_id])
    
    @classmethod
    def get_available_gpu_for_node(cls, node_id):
        total_available = 0
        for gpunum, gpustatus in cls.__GPUs[node_id].iteritems():
            if gpustatus == "available":
                total_available += 1
            
        return total_available