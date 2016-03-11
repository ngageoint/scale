package main

import (
    "github.com/codegangsta/cli"
    "github.com/ngageoint/scale/goscale"
    "github.com/op/go-logging"
    "github.com/fatih/color"
    "os"
)

// setup logging
var log = logging.MustGetLogger("goscale")
var logformat = logging.MustStringFormatter(
        `%{color}%{level:.4s}   %{message}%{color:reset}`,
)

func main() {
    // format log output
    logback := logging.NewLogBackend(os.Stderr, "", 0)
    logformatter := logging.NewBackendFormatter(logback, logformat)
    logging.SetBackend(logformatter)

    app := cli.NewApp()
    app.Name = "goscale"
    app.Version = "0.1.0"
    app.Usage = "Command line tool to access Scale"
    app.Flags = []cli.Flag{
        cli.StringFlag{
            Name: "url",
            Usage: "Scale API URL",
            EnvVar: "SCALE_URL",
        },
    }
    app.Commands = []cli.Command{
        {
            Name:    "workspaces",
            Aliases: []string{"workspace", "ws"},
            Usage:   "Workspace information and modification",
            Subcommands: []cli.Command{
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
                    Action: func(c *cli.Context) {
                        max := c.Int("max")
                        url := c.GlobalString("url")
                        workspaces, err := goscale.GetWorkspaceList(url, max)
                        if err != nil {
                            log.Fatal(err)
                        }
                        for _, workspace := range(workspaces) {
                            if workspace.Is_active {
                                color.Green(workspace.String())
                            } else {
                                color.White(workspace.String())
                            }
                        }
                    },
                },
            },
        },
    }

    app.Run(os.Args)
}
