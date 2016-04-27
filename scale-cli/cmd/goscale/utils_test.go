package main

import (
    "testing"
    "io/ioutil"
    "path/filepath"
    "os"
    "reflect"
)

const json_test_data = `{
    "version":"1.0.0",
    "name":"foo",
    "interface":{
        "version":"1.0.0"
    },
    "list":[1,2,3]}`
const yaml_test_data = `---
version: '1.0.0'
name: foo
interface:
  version: '1.0.0'
list:
  - 1
  - 2
  - 3
`

type test_data_type struct {
    Version     string `json:"version"`
    Name        string `json:"name"`
    Interface   `json:"interface"`
    List        []int `json:"list"`
}
type Interface   struct {
    Version    string `json:"version"`
}

var test_data = test_data_type{"1.0.0", "foo", Interface{"1.0.0"}, []int{1,2,3}}

func TestParse_json_or_yaml(t *testing.T) {
    tmpdir, err := ioutil.TempDir("", "utils_test")
    if err != nil {
        t.Error(err)
    }
    defer os.RemoveAll(tmpdir)

    base_name := filepath.Join(tmpdir, "test")

    var pdata test_data_type
    // test no files
    err = Parse_json_or_yaml(base_name, &pdata)
    if err == nil {
        t.Error("Expected a failed parse")
    }

    // test json
    json_name := filepath.Join(tmpdir, "test.json")
    json_file, err := os.Create(json_name)
    if err != nil {
        t.Error(err)
    }
    _, err = json_file.Write([]byte(json_test_data))
    if err != nil {
        t.Error(err)
    }
    json_file.Close()
    err = Parse_json_or_yaml(base_name, &pdata)
    if err != nil {
        t.Error(err)
    }

    if !reflect.DeepEqual(pdata, test_data) {
        t.Error("Structs not equal:", pdata, "!=", test_data)
    }

    // test json specifying an explicit filename
    pdata = test_data_type{}
    err = Parse_json_or_yaml(json_name, &pdata)
    if err != nil {
        t.Error(err)
    }

    if !reflect.DeepEqual(pdata, test_data) {
        t.Error("Structs not equal:", pdata, "!=", test_data)
    }

    // test yaml
    yaml_name := filepath.Join(tmpdir, "test.yml")
    yaml_file, err := os.Create(yaml_name)
    if err != nil {
        t.Error(err)
    }
    _, err = yaml_file.Write([]byte(yaml_test_data))
    if err != nil {
        t.Error(err)
    }
    yaml_file.Close()
    var pdata2 test_data_type
    err = Parse_json_or_yaml(base_name, &pdata2)
    if err == nil {
        t.Error("Expected a failed parse")
    }
    os.Remove(json_name)
    err = Parse_json_or_yaml(base_name, &pdata2)
    if err != nil {
        t.Error(err)
    }

    if !reflect.DeepEqual(pdata2, test_data) {
        t.Error("Structs not equal:", pdata2, "!=", test_data)
    }

    // test yaml specifying an explicit filename
    pdata2 = test_data_type{}
    err = Parse_json_or_yaml(yaml_name, &pdata2)
    if err != nil {
        t.Error(err)
    }

    if !reflect.DeepEqual(pdata2, test_data) {
        t.Error("Structs not equal:", pdata2, "!=", test_data)
    }
}
