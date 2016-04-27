package scalecli

import (
    "testing"
    "encoding/json"
    "reflect"
)

const interface_json_data = `{
   "version": "1.0",
   "command": "python make_geotiff.py",
   "command_arguments": "${image} ${georeference_data} ${job_output_dir}",
   "input_data": [
      {
         "name": "image",
         "type": "file",
         "media_types": [
            "image/png"
         ]
      },
      {
         "name": "georeference_data",
         "type": "file",
         "media_types": [
            "text/csv"
         ]
      }
   ],
   "output_data": [
      {
         "name": "geo_image",
         "type": "file",
         "media_type": "image/tiff"
      }
   ]
}`

var interface_test_data = JobTypeInterface{
   Version: "1.0",
   Command: "python make_geotiff.py",
   CommandArguments: "${image} ${georeference_data} ${job_output_dir}",
   InputData: []InputData{ InputData{
         Name: "image",
         Type: "file",
         MediaTypes: []string{"image/png"},
      },
      InputData{
         Name: "georeference_data",
         Type: "file",
         MediaTypes: []string{"text/csv"},
      }},
   OutputData: []OutputData{ OutputData{
         Name: "geo_image",
         Type: "file",
         MediaType: "image/tiff",
      }},
}

func TestJobInterface(t *testing.T) {
    var pdata JobTypeInterface
    err := json.Unmarshal([]byte(interface_json_data), &pdata)
    if err != nil {
        t.Error(err)
    }
    if !reflect.DeepEqual(pdata, interface_test_data) {
        t.Error("Structs not equal:", pdata, "!=", interface_test_data)
    }
}
