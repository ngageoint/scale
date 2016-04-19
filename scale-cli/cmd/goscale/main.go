package main

import (
    "github.com/codegangsta/cli"
    "github.com/op/go-logging"
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
            Name:    "jobs",
            Aliases: []string{"job"},
            Usage:   "Job and job type commands",
            Subcommands: Jobs_commands,
        },
        {
            Name:    "workspaces",
            Aliases: []string{"workspace", "ws"},
            Usage:   "Workspace information and modification",
            Subcommands: Workspaces_commands,
        },
    }

    app.Run(os.Args)
}
