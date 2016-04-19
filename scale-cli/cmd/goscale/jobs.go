package main

import (
    "github.com/codegangsta/cli"
    //"github.com/ngageoint/scale/scale-cli"
)

func jobs_template(c *cli.Context) {
    template := c.String("template")
    if template == "" {
    } else {
        log.Warning("External templates not yet supported. Using default template")
        template = ""
    }
}

var Jobs_commands = []cli.Command{
    {
        Name: "init",
        Aliases: []string{"i"},
        Usage: "Initialize a new job type in the current or specified directory. Does not modify scale.",
        ArgsUsage: "[path]",
        Flags: []cli.Flag{
            cli.StringFlag{
                Name: "template",
                Usage: "Specifies a template for the new job type. If not specified, a default will be used.",
            },
        },
        Action: jobs_template,
    },
}
