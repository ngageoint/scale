package main

import (
    "github.com/ngageoint/scale/scale-cli"
    "github.com/codegangsta/cli"
    "github.com/fatih/color"
)

func workspaces_list(c *cli.Context) error {
    max := c.Int("max")
    url := c.GlobalString("url")
    if url == "" {
        return cli.NewExitError("A URL must be provided with the SCALE_URL environment variable or the --url argument", 1)
    }
    workspaces, err := scalecli.GetWorkspaceList(url, max)
    if err != nil {
        return cli.NewExitError(err.Error(), 1)
    }
    for _, workspace := range(workspaces) {
        if workspace.Is_active {
            color.Green(workspace.String())
        } else {
            color.White(workspace.String())
        }
    }
    return nil
}

func workspaces_create(c *cli.Context) error {
    url := c.GlobalString("url")
    if url == "" {
        return cli.NewExitError("A URL must be provided with the SCALE_URL environment variable or the --url argument", 1)
    }
    data_file := c.String("data")
    var ws_data scalecli.NewWorkspace
    err := Parse_json_or_yaml(data_file, &ws_data)
    if err != nil {
        return cli.NewExitError(err.Error(), 1)
    }
    if ws_data.Version == "" {
        ws_data.Version = "1.0"
    }
    warnings, err := scalecli.CreateWorkspace(url, ws_data)
    if err != nil {
        return cli.NewExitError(err.Error(), 1)
    }
    if warnings != "" {
        return cli.NewExitError(warnings, 1)
    }
    return nil
}

var Workspaces_commands = []cli.Command{
    {
        Name: "list",
        Aliases: []string{"ls"},
        Usage: "List all workspaces",
        Flags: []cli.Flag{
            cli.IntFlag{
                Name: "max",
                Value: 100,
                Usage: "Maximum number of items to list",
            },
        },
        Action: workspaces_list,
    },
    {
        Name: "create",
        Aliases: []string{"c"},
        Usage: "Create a new workspace",
        Flags: []cli.Flag {
            cli.StringFlag{
                Name: "data, d",
                Usage: "Job data file (json or yaml).",
            },
        },
        Action: workspaces_create,
    },
}

