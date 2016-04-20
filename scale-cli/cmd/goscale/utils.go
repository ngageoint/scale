package main

import (
    "strings"
    "os"
    "strconv"
    "errors"
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
