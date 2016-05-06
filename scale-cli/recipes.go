package scalecli

import (
    "gopkg.in/resty.v0"
    "fmt"
    "encoding/json"
)

type RecipeData struct {
    Version         string `json:"version,omitempty"`
    InputData       []RecipeInputData `json:"input_data,omitempty"`
    WorkspaceId     int `json:"workspace_id"`
}

type RecipeInputData struct {
    Name            string `json:"name"`
    Value           string `json:"value,omitempty"`
    FileId          int `json:"file_id,omitempty"`
    FileIds         []int `json:"file_ids,omitempty"`
}

type RecipeType struct {
    Id                  int `json:"id,omitempty"`
    Name                string `json:"name"`
    Version             string `json:"version"`
    Title               string `json:"title,omitempty"`
    Description         string `json:"description,omitempty"`
}

func GetRecipeTypes(base_url string) (recipe_types []RecipeType, err error) {
    request := resty.R()
    resp, err := request.SetHeader("Accept", "application/json").
                         Get(base_url + "/recipe-types/")
    if resp == nil {
        return nil, fmt.Errorf("Unknown error")
    } else if resp.StatusCode() != 200 {
        return nil, fmt.Errorf("http: server error %s", resp.String())
    }
    var rtlist struct {
        Count            int
        Next             string
        Previous         string
        Results          []RecipeType
    }
    err = json.Unmarshal([]byte(resp.String()), &rtlist)
    if err != nil {
        return nil, err
    }
    return rtlist.Results, nil
}

func GetRecipeTypeDetails(base_url string, id int) (recipe_type RecipeType, resp_code int, err error) {
    resp, err := resty.R().SetHeader("Accept", "application/json").
                           Get(fmt.Sprintf("%s/recipe-types/%d/", base_url, id))
    if resp == nil {
        return
    } else if resp.StatusCode() != 200 {
        resp_code = resp.StatusCode()
        err = fmt.Errorf("http: server error %s", resp.String())
        return
    }
    err = json.Unmarshal([]byte(resp.String()), &recipe_type)
    return
}

func RunRecipe(base_url string, recipe_type_id int, recipe_data RecipeData) (update_location string, err error) {
    var new_recipe_data = struct {
            RecipeTypeId      int `json:"recipe_type_id"`
            RecipeData        RecipeData `json:"recipe_data"`
        }{ recipe_type_id, recipe_data }
    json_data, err := json.Marshal(new_recipe_data)
    if err != nil {
        return
    }
    resp, err := resty.R().SetHeaders(map[string]string{
            "Accept":"application/json",
            "Content-type":"application/json",
        }).SetBody(json_data).Post(base_url + "/queue/new-recipe/")
    if resp == nil && err != nil {
        return
    } else if resp == nil {
        err = fmt.Errorf("Unknown error")
        return
    } else if resp.StatusCode() != 201 {
        err = fmt.Errorf(resp.String())
        return
    }
    update_location = resp.Header()["Location"][0]
    return
}