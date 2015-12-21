import storage.models
import job.models
import ingest.models
from ingest.triggers.ingest_rule import IngestTriggerRule
from recipe.configuration.definition.recipe_definition import RecipeDefinition
import recipe.models
import storage.models
import trigger.models

# Workspaces
if not storage.models.Workspace.objects.filter(name="raw").exists():
    storage.models.Workspace.objects.create(name="raw", title="raw", description="Raw ingested data", json_config={
        "version": "1.0", "broker": {"mount": "10.4.4.10:/raw", "type": "nfs"}}).save()

if not storage.models.Workspace.objects.filter(name="products").exists():
    storage.models.Workspace.objects.create(name="products", title="products", description="Product storage", json_config={
        "version": "1.0", "broker": {"mount": "10.4.4.10:/products", "type": "nfs"}}).save()

# Job types
if not job.models.JobType.objects.filter(name="landsat-parse").exists():
    jt = job.models.JobType.objects.create_job_type("landsat-parse", "1.0.0", "Parse landsat multi-tif files in tar.gz archives",
        "10.4.4.10:5000/landsat-parse_1.0:dev",
            {"output_data": [
                {"media_type": "image/tiff", "required": True, "type": "file", "name": "multispectral"},
                {"media_type": "image/tiff", "required": True, "type": "file", "name": "panchromatic"},
                {"media_type": "image/tiff", "required": True, "type": "file", "name": "thermal"}
            ],
            "shared_resources": [],
            "command_arguments": "${infile} ${job_output_dir}",
            "input_data": [
                {"media_types": ["application/octet-stream"], "required": True, "type": "file", "name": "infile"}],
            "version": "1.0", "command": "./parse_landsat.sh"
        }, 200, 300, 3, 0.25, 512., 2048., None)
    jt.title = "Landsat Parse"
    jt.save()
if not job.models.JobType.objects.filter(name="landsat-ndwi").exists():
    jt = job.models.JobType.objects.create_job_type("landsat-ndwi", "1.0.0", "Perform NDWI on landsat 8 data.",
        "10.4.4.10:5000/landsat-ndwi_1.0:dev",
            {"output_data": [
                {"media_type": "image/tiff", "required": True, "type": "file", "name": "ndwi"}],
            "shared_resources": [],
            "command_arguments": "${msi} ${job_output_dir}",
            "input_data": [
                {"media_types": ["image/tiff"], "required": True, "type": "file", "name": "msi"}],
            "version": "1.0", "command": "python landsat_ndwi.py"
        }, 250, 300, 3, 0.5, 512., 2048., None)
    jt.title = "Landsat NDWI"
    jt.save()

# Recipes
if not recipe.models.RecipeType.objects.filter(name="landsat").exists():
    r = recipe.models.RecipeType.objects.create_recipe_type("landsat", "1.0.0", "Landsat processing",
            "Perform standard Landsat ingest processing", RecipeDefinition({
                "version": "1.0",
                "input_data": [
                    {
                        "name": "infile",
                        "type": "file",
                        "media_types": ["application/x-tar"]
                    }
                ],
                "jobs": [
                    {
                        "name": "parse",
                        "job_type": {
                            "name": "landsat-parse",
                            "version": "1.0.0"
                        },
                        "recipe_inputs": [
                            {
                                "recipe_input": "infile",
                                "job_input": "infile"
                            }
                        ]
                    },
                    {
                        "name": "ndwi",
                        "job_type": {
                            "name": "landsat-ndwi",
                            "version": "1.0.0"
                        },
                        "dependencies": [
                            {
                                "name": "parse",
                                "connections": [
                                    {"output": "multispectral", "input": "msi"}
                                ]
                            }
                        ]
                    }
                ]
            }), None)

# Triggers
if not trigger.models.TriggerRule.objects.filter(name="landsat-parse").exists():
    tr = IngestTriggerRule({
        "version": "1.0",
        "trigger": {
            "media_type": "application/x-tar",
            "data_types": ["landsat"]
        },
        "create": {
            "recipes": [
                {
                    "recipe_type": {
                        "name": "landsat",
                        "version": "1.0.0"
                    },
                    "file_input_name": "infile",
                    "workspace_name": "products"
                }
            ]
        }
    }).save_to_db()
    tr.name="landsat-parse"
    tr.save()

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
	    "mount": "10.4.4.10:/ingest",
	    "transfer_suffix": "_tmp",
	    "version": "1.0"
	}).save()

# Country Data
if storage.models.CountryData.objects.count() == 0:
    from osgeo import ogr
    import os
    from django.contrib.gis.geos.geometry import GEOSGeometry
    from datetime import datetime

    driver = ogr.GetDriverByName('ESRI Shapefile')
    ds = driver.Open('/tmp/TM_WORLD_BORDERS-0.3.shp', 0)
    mtime = datetime.utcfromtimestamp(os.stat('/tmp/TM_WORLD_BORDERS-0.3.shp').st_mtime)
    layer = ds.GetLayer()
    for feature in layer:
        name = feature.GetFieldAsString('NAME')
        print('Importing %s' % name)
        fips = feature.GetFieldAsString('FIPS')
        iso2 = feature.GetFieldAsString('ISO2')
        iso3 = feature.GetFieldAsString('ISO3')
        iso_num = feature.GetFieldAsString('UN')
        geom = feature.GetGeometryRef()
        wkt = geom.ExportToWkt()
        storage.models.CountryData.objects.create(name=name,
                                                  fips=fips,
                                                  iso2=iso2,
                                                  iso3=iso3,
                                                  iso_num=iso_num,
                                                  border=GEOSGeometry(wkt),
                                                  effective=mtime).save()