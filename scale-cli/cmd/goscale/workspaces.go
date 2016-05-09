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
}

