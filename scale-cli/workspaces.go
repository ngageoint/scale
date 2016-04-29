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
        return nil, fmt.Errorf("http: server error %s", resp.String())
    }
    var wslist struct {
        Count            int
        Next             string
        Previous         string
        Results       []Workspace
    }
    err = json.Unmarshal([]byte(resp.String()), &wslist)
    if err != nil {
        return nil,err
    }
    return wslist.Results, nil
}

func (w *Workspace) String() string {
    return fmt.Sprintf("Workspace [%4d]: %-10s  (title: %-10s) (desciption: %-30s)", w.Id, w.Name, w.Title, w.Description)
}
