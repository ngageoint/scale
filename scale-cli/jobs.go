package scalecli

import (
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
    ErrorMapping        ErrorMapping `json:"error_mapping,omitempty"`
    TriggerRule         TriggerRule `json:"trigger_rule,omitempty"`
}

