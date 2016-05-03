package main

import (
    "github.com/codegangsta/cli"
    "github.com/op/go-logging"
    "os"
    "os/user"
    "path/filepath"
    "gopkg.in/yaml.v2"
)

// setup logging
var log = logging.MustGetLogger("goscale")
var logformat = logging.MustStringFormatter(
        `%{color}%{level:.4s}   %{message}%{color:reset}`,
)

func load_config_file(fname string) (config map[string]interface{}, err error) {
    yaml_stat, err := os.Stat(fname)
    if err != nil {
        return
    }
    f, err := os.Open(fname)
    defer f.Close()
    if err != nil {
        return
    }
    buf := make([]byte, yaml_stat.Size())
    f.Read(buf)
    err = yaml.Unmarshal(buf, &config)
    return
}

func main() {
    // format log output
    logback := logging.NewLogBackend(os.Stderr, "", 0)
    logformatter := logging.NewBackendFormatter(logback, logformat)
    logging.SetBackend(logformatter)

    user, err := user.Current()
    if err != nil {
        log.Error(err)
    }

    // hard defaults for config values...prevents type assertions on nil
    config := map[string]interface{} {
        "registry": "",
        "tag": "",
        "url": "",
    }

    // ignore the error. if the file isn't found, just continue
    user_config, _ := load_config_file(filepath.Join(user.HomeDir, ".scaleconf"))
    for k, v := range user_config {
        config[k] = v
    }

    app := cli.NewApp()
    app.Name = "goscale"
    app.Version = "0.1.0"
    app.Usage = "Command line tool to access Scale"
    app.Flags = []cli.Flag{
        cli.StringFlag{
            Name: "url",
            Usage: "Scale API URL",
            EnvVar: "SCALE_URL",
            Value: config["url"].(string),
        },
        cli.StringFlag{
            Name: "registry, r",
            Usage: `Optional docker registry to prepend to docker image names. \
               This should not be used if you've already included the registry in the image name.`,
            EnvVar: "DOCKER_REGISTRY",
            Value: config["registry"].(string),
        },
        cli.StringFlag{
            Name: "tag, t",
            Usage: `Optional docker tag to append to docker image names. \
               This should not be used if you've already included the tag in the image name.`,
            EnvVar: "DOCKER_TAG",
            Value: config["tag"].(string),
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
            Name:    "recipes",
            Aliases: []string{"recipe"},
            Usage:   "Recipe commands",
            Subcommands: Recipes_commands,
        },
        {
            Name:    "strike",
            Usage:   "Strike commands",
            Subcommands: Strike_commands,
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
