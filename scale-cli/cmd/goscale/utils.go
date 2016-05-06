package main

import (
    "strings"
    "os"
    "strconv"
    "errors"
    "syscall"
    "github.com/ghodss/yaml"
    "encoding/json"
)

var ErrNotFound = errors.New("template not found in $SCALE_TEMPLATE_PATH")
type Error struct {
    Name string
    Err  error
}

 func (e *Error) Error() string {
     return strconv.Quote(e.Name) + ": " + e.Err.Error()
 }

func find_template(path string) error {
    d, err := os.Stat(path)
    if err != nil {
        return err
    }
    if m := d.Mode(); m.IsDir() && m&0555 != 0 {
        return nil
    }
    return os.ErrPermission
}

func find_template_in_path(template_name string, template_path string) (string, error) {
    if strings.Contains(template_name, "/") {
        err := find_template(template_name)
        if err == nil {
            return template_name, nil
        }
    }
    for _, dir := range strings.Split(template_path, ":") {
        if dir == "" {
            dir = "/usr/share/scale/templates"
        }
        path := dir + "/" + template_name
        if err := find_template(path); err == nil {
            return path, nil
        }
    }
    return "", &Error{template_name, ErrNotFound}
}

func Parse_json_or_yaml(basename string, parsed_data interface{}) error {
    // check the basename first
    _, err := os.Stat(basename)
    var json_file, yaml_file string
    if err == nil {
        // file exists, try it as both json and yaml
        json_file = basename
        yaml_file = basename
    } else {
        json_file = basename + ".json"
        yaml_file = basename + ".yml"
    }
    json_stat, err := os.Stat(json_file)
    if err != nil {
        if e, ok := err.(*os.PathError); ok && e.Err == syscall.ENOENT {
            json_stat = nil
        } else {
            // error stating the file
            return err
        }
    }
    yaml_stat, err := os.Stat(yaml_file)
    if err != nil {
        if e, ok := err.(*os.PathError); ok && e.Err == syscall.ENOENT {
            yaml_stat = nil // not present
        } else {
            // error stating the file
            return err
        }
    }
    if yaml_stat == nil {
        yaml_file = basename + ".yaml"
        yaml_stat, err = os.Stat(yaml_file)
        if err != nil {
            if e, ok := err.(*os.PathError); ok && e.Err == syscall.ENOENT {
                yaml_stat = nil // not present
            } else {
                // error stating the file
                return err
            }
        }
    }
    if json_stat == nil && yaml_stat == nil {
        return errors.New("Neither JSON nor YAML files exist. " + basename)
    }
    if json_file != yaml_file && json_stat != nil && yaml_stat != nil {
        return errors.New("Both JSON and YAML files exists. " + basename)
    }
    var json_data []byte
    if yaml_stat != nil {
        tmp, err := os.Open(yaml_file)
        if err != nil {
            return err
        }
        data := make([]byte, yaml_stat.Size())
        tmp.Read(data)
        tmp.Close()
        json_data, err = yaml.YAMLToJSON(data)
        if err != nil && json_file != yaml_file {
            return err
        }
    }
    if json_data == nil && json_stat != nil {
        tmp, err := os.Open(json_file)
        if err != nil {
            return err
        }
        json_data = make([]byte, json_stat.Size())
        tmp.Read(json_data)
        tmp.Close()
    }
    err= json.Unmarshal(json_data, &parsed_data)
    return err
}
