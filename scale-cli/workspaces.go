package scalecli

import(
   "gopkg.in/resty.v0"
   "fmt"
   "encoding/json"
)

type Workspace struct {
   Id               int
   Name             string
   Title            string
   Description      string
   Base_url         string
   Is_active        bool
   Used_size        float32
   Total_size       float32
   Created          string
   Archived         string
   Last_modified    string
}

type NewWorkspace struct {
    Version         string          `json:"version,omitempty"`
    Name            string          `json:"name"`
    Title           string          `json:"title,omitempty"`
    Description     string          `json:"description,omitempty"`
    Base_url        string          `json:"base_url,omitempty"`
    Is_active       bool            `json:"is_active"`
    Configuration   struct {
        Broker      interface{}     `json:"broker"`
    }                               `json:"json_config"`

}

func GetWorkspaceList(base_url string, max_count int) (workspaces []Workspace, err error) {
    resp, err := resty.R().
         SetQueryParams(map[string]string{
             "page_size":fmt.Sprintf("%d", max_count),
         }).
         SetHeader("Accept", "application/json").
         Get(base_url+"/workspaces/")

    if resp == nil {
        return nil, fmt.Errorf("Unknown error")
    } else if resp.StatusCode() != 200 {
        return nil, fmt.Errorf("http: server error %s -- %s", resp.String(), base_url+"/workspaces/")
    }
    var wslist struct {
        Count            int
        Next             string
        Previous         string
        Results          []Workspace
    }
    err = json.Unmarshal([]byte(resp.String()), &wslist)
    if err != nil {
        return nil,err
    }
    return wslist.Results, nil
}

func CreateWorkspace(base_url string, workspace_config NewWorkspace) (warnings string, err error) {
    json_data, err := json.Marshal(workspace_config)
    if err != nil {
        return
    }
    resp, err := resty.R().
        SetHeaders(map[string]string{
            "Accept":"application/json",
            "Content-type":"application/json",
        }).SetBody(json_data).Post(base_url+"/workspaces/")
    if resp == nil {
        err = fmt.Errorf("Unknown error")
        return
    }
    var warning_struct struct {
        Detail string `json:"detail"`
    }
    err = json.Unmarshal([]byte(resp.String()), &warning_struct)
    if err != nil {
        warnings = resp.String()
        err = nil
        return
    }
    warnings = warning_struct.Detail
    return
}

func (w *Workspace) String() string {
    return fmt.Sprintf("Workspace [%4d]: %-10s  (title: %-10s) (desciption: %-30s)", w.Id, w.Name, w.Title, w.Description)
}
