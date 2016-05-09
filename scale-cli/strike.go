package scalecli

import (
    "gopkg.in/resty.v0"
    "fmt"
    "encoding/json"
)

type StrikeIngestFile struct {
    FileNameRegex   string `json:"filename_regex"`
    DataTypes       []string `json:"data_types,omitempty"`
    WorkspacePath   string `json:"workspace_path"`
    WorkspaceName   string `json:"workspace_name"`
}

type StrikeConfiguration struct {
    Version         string `json:"version,omitempty"`
    Mount           string `json:"mount"`
    TransferSuffix  string `json:"transfer_suffix"`
    FilesToIngest   []StrikeIngestFile `json:"files_to_ingest"`
}

type StrikeData struct {
    Name            string `json:"name"`
    Title           string `json:"title,omitempty"`
    Description     string `json:"description,omitempty"`
    Configuration   StrikeConfiguration `json:"configuration"`
}

func CreateStrikeProcess(base_url string, strike_data StrikeData) (strike_id int, err error) {
    json_data, err := json.Marshal(strike_data)
    if err != nil {
        return
    }
    resp, err := resty.R().SetHeaders(map[string]string{
            "Accept":"application/json",
            "Content-type":"application/json",
        }).SetBody(json_data).Post(base_url + "/strike/create/")
    if resp == nil && err != nil {
        return
    } else if resp == nil {
        err = fmt.Errorf("Unknown error")
        return
    } else if resp.StatusCode() != 200 {
        err = fmt.Errorf(resp.String())
        return
    }
    var resp_data map[string]interface{}
    err = json.Unmarshal([]byte(resp.Body()), &resp_data)
    if err != nil {
        return
    }
    tmp, ok := resp_data["strike_id"].(float64)
    if ok {
        strike_id = int(tmp)
    } else {
        err = fmt.Errorf("Unknown response %s", resp.Body())
    }
    return
}