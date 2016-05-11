package main

import (
    "github.com/ngageoint/scale/scale-cli"
    "github.com/codegangsta/cli"
    "github.com/fatih/color"
    "fmt"
)

func strike_create(c *cli.Context) error {
    url := c.GlobalString("url")
    if url == "" {
        return cli.NewExitError("A URL must be provided with the SCALE_URL environment variable or the --url argument", 1)
    }
    data_file := c.String("data")
    var strike_data scalecli.StrikeData
    err := Parse_json_or_yaml(data_file, &strike_data)
    if err != nil {
        return cli.NewExitError(err.Error(), 1)
    }
    strike_process_id, err := scalecli.CreateStrikeProcess(url, strike_data)
    if err != nil {
        return cli.NewExitError(err.Error(), 1)
    }
    color.Blue(fmt.Sprintf("Strike proess %d created.", strike_process_id))
    return nil
}

var Strike_commands = []cli.Command{
    {
        Name: "create",
        Aliases: []string{"c", "new"},
        Usage: "Create and register a new strike process.",
        Flags: []cli.Flag{
            cli.StringFlag{
                Name: "data, d",
                Usage: "Strike data file (json or yaml).",
            },
        },
        Action: strike_create,
    },
}
