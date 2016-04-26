package scalecli

import (
)
import (
    "gopkg.in/resty.v0"
    "fmt"
    "encoding/json"
)

type JobTypeInterface struct {
    Version          string `json:"version,omitempty"`
    Command          string `json:"command"`
    CommandArguments string `json:"command_arguments"`
    InputData        []InputData `json:"input_data,omitempty"`
    OutputData       []OutputData `json:"output_data,omitempty"`
    SharedResources  []SharedResources `json:"shared_resources,omitempty"`
}

type InputData struct {
    Name            string `json:"name"`
    Type            string `json:"type"`
    Required        bool `json:"required,omitempty"`
    MediaTypes      []string `json:"media_types,omitempty"`
}

type OutputData struct {
    Name            string `json:"name"`
    Type            string `json:"type"`
    Required        bool `json:"required,omitempty"`
    MediaType       string `json:"media_type,omitempty"`
}

type SharedResources struct {
    Name            string `json:"name"`
    Type            string `json:"type"`
    Required        bool `json:"required,omitempty"`
}

type ErrorMapping struct {
    Version             string `json:"version"`
    ExitCodes           map[string][]string `json:"exit_codes"`
}

type TriggerRule struct {
    Version       string `json:"version,omitempty"`
    Type          string `json:"type"`
    IsActive      bool   `json:"is_active,omitempty"`
    Configuration interface{} `json:"configuration"`
}

type JobType struct {
    Id                  int `json:"id,omitempty"`
    Name                string `json:"name"`
    Version             string `json:"version"`
    Title               string `json:"title,omitempty"`
    Description         string `json:"description,omitempty"`
    Category            string `json:"category,omitempty"`
    AuthorName          string `json:"author_name,omitempty"`
    AuthorUrl           string `json:"author_url,omitempty"`
    IsLongRunning       bool   `json:"is_long_running,omitempty"`
    IsPaused            bool   `json:"is_paused,omitempty"`
    IconCode            string `json:"icon_code,omitempty"`
    DockerImage         string `json:"docker_image"`
    Priority            int    `json:"priority,omitempty"`
    Timeout             int    `json:"timeout,omitempty"`
    MaxScheduled        int    `json:"max_scheduled,omitempty"`
    MaxTries            int    `json:"max_tries,omitempty"`
    CpusRequired        float32 `json:"cpus_required,omitempty"`
    MemRequired         float32 `json:"mem_required,omitempty"`
    DiskOutConstRequired float32 `json:"disk_out_const_required,omitempty"`
    DiskOutMultRequired float32 `json:"disk_out_mult_required,omitempty"`
    Interface           JobTypeInterface `json:"interface"`
    ErrorMapping        *ErrorMapping `json:"error_mapping,omitempty"`
    TriggerRule         *TriggerRule `json:"trigger_rule,omitempty"`
}

func GetJobTypes(base_url string, name string) (job_types []JobType, err error) {
    request := resty.R()
    if name != "" {
        request.SetQueryParam("name", name)
    }
    resp, err := request.SetHeader("Accept", "application/json").
                         Get(base_url + "/job-types/")
    if resp == nil {
        return nil, fmt.Errorf("Unknown error")
    } else if resp.StatusCode() != 200 {
        return nil, fmt.Errorf("http: server error %s", resp.String())
    }
    var jtlist struct {
        Count            int
        Next             string
        Previous         string
        Results          []JobType
    }
    err = json.Unmarshal([]byte(resp.String()), &jtlist)
    if err != nil {
        return nil, err
    }
    return jtlist.Results, nil
}

func ValidateJobType(base_url string, job_type JobType) (warnings string, err error) {
    json_data, err := json.Marshal(job_type)
    if err != nil {
        return
    }
    resp, err := resty.R().SetHeaders(map[string]string{
            "Accept": "application/json",
            "Content-type": "application/json",
        }).SetBody(json_data).Post(base_url + "/job-types/validation/")
    if resp == nil {
        err = fmt.Errorf("Unknown error")
        return
    }
    var warning_struct struct {
        Detail string `json:"detail"`
    }
    err = json.Unmarshal([]byte(resp.String()), &warning_struct)
    if err != nil {
        return
    }
    warnings = warning_struct.Detail
    return
}

func CreateJobType(base_url string, job_type JobType) error {
    json_data, err := json.Marshal(job_type)
    if err != nil {
        return err
    }
    resp, err := resty.R().SetHeaders(map[string]string{
            "Accept":"application/json",
            "Content-type":"application/json",
        }).SetBody(json_data).Post(base_url + "/job-types/")
    if resp == nil {
        return fmt.Errorf("Unknown error")
    } else if resp.StatusCode() != 201 {
        return fmt.Errorf("http: server error %s", resp.String())
    }
    return nil
}

func UpdateJobType(base_url string, job_type_id int, job_type JobType) error {
    json_data, err := json.Marshal(job_type)
    if err != nil {
        return err
    }
    resp, err := resty.R().SetHeaders(map[string]string{
            "Accept":"application/json",
            "Content-type":"application/json",
        }).SetBody(json_data).Patch(fmt.Sprintf("%s/job-types/%d/", base_url, job_type_id))
    if resp == nil {
        return fmt.Errorf("Unknown error")
    } else if resp.StatusCode() != 200 {
        return fmt.Errorf("http: server error %s", resp.String())
    }
    return nil
}
