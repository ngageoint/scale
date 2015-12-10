import storage.models
import job.models
import ingest.models

# Workspaces
if not storage.models.Workspace.objects.filter(name="raw").exists():
    storage.models.Workspace.objects.create(name="raw", title="raw", description="Raw ingested data", json_config={
        "version": "1.0", "broker": {"mount": "10.4.4.10:/exports/raw", "type": "nfs"}}).save()

if not storage.models.Workspace.objects.filter(name="products").exists():
    storage.models.Workspace.objects.create(name="products", title="products", description="Product storage", json_config={
        "version": "1.0", "broker": {"mount": "10.4.4.10:/exports/products", "type": "nfs"}}).save()

# Job types
if not job.models.JobType.objects.filter(name="landsat-parse").exists():
    job.models.JobType.objects.create_job_type("landsat-parse", "1.0", "Parse landsat multi-tif files in tar.gz archives",
        "10.4.4.10:5000/landsat-parse_1.0:dev",
            {"output_data": [
                {"media_type": "image/tiff", "required": True, "type": "file", "name": "geo_image"}],
            "shared_resources": [],
            "command_arguments": "${infile} ${job_output_dir}",
            "input_data": [
                {"media_types": ["application/octet-stream"], "required": True, "type": "file", "name": "infile"}],
            "version": "1.0", "command": "./parse_landsat.sh"
        }, 200, 300, 3, 0.25, 512., 2048., None).save()

# Strike process
if not ingest.models.Strike.objects.filter(name="landsat").exists():
    ingest.models.Strike.objects.create_strike_process("landsat", "Landsat", "Landsat GeoTIFF Ingest",
	{
	    "files_to_ingest": [
		{
		    "data_types": [
			"landsat"
		    ],
		    "filename_regex": r".*tar.gz",
		    "workspace_name": "raw",
		    "workspace_path": "landsat"
		}
	    ],
	    "mount": "10.4.4.10:/exports/ingest",
	    "transfer_suffix": "_tmp",
	    "version": "1.0"
	}).save()
