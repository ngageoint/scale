package main

import (
    "github.com/codegangsta/cli"
    "os"
    "strconv"
    "syscall"
    "path/filepath"
    "text/template"
    "strings"
)

// hardcoded defaults
var defaults = map[string]string{
    "Dockerfile": `FROM {{ .baseimage }}
MAINTAINER {{ .maintainer }}
COPY entryPoint.sh ./
ENTRYPOINT ["./entryPoint.sh"]
`,
    "entryPoint.sh": `#!/bin/sh -x

# generate result manifest
DATE_STARTED=$(stat -c "%y" $1)"Z"
cat > $2/results_manifest.json << EOF
{ "version": "1.1",
}
EOF
cat $2/results_manifest.json
`,
}

func jobs_template(c *cli.Context) {
    // locate the template...if none is specified, fall back to a hard coded default
    template_name := c.String("template")
    if template_name != "" {
        template_path := c.GlobalString("template-path")
        tmp, err := find_template_in_path(template_name, template_path)
        if err != nil {
            log.Error(err)
            return
        }
        template_name = tmp
    }

    // setup the target dir
    target_dir := "."
    if c.NArg() > 0 {
        target_dir = c.Args()[0]
    }
    d, err := os.Stat(target_dir)
    if err == nil {
        if !d.Mode().IsDir() {
            log.Error("Target exists and is not a directory.")
            return
        } else if c.Bool("f") {
            log.Warning("Target directory",strconv.Quote(target_dir),"exists. Overriting contents.")
        } else {
            log.Error("Target directory", strconv.Quote(target_dir), "exists. Use -f to overrite.")
            return
        }
    } else {
        if e, ok := err.(*os.PathError); ok && e.Err == syscall.ENOENT {
            os.MkdirAll(target_dir, 0755)
        } else {
            log.Error(err)
            return
        }
    }

    context := map[string]string{}
    for _, val := range c.StringSlice("arg") {
        tmp := strings.Split(val, "=")
        if len(tmp) != 2 {
            log.Warning("Invalid arg", val)
        } else {
            context[tmp[0]] = tmp[1]
        }
    }

    // use the hardcoded defaults
    if template_name == "" {
        for fname, val := range defaults {
            log.Info("Processing", fname)
            target_path := filepath.Join(target_dir, fname)
            // process template
            tmpl, err := template.New(fname).Parse(val)
            if err != nil {
                log.Error(err)
                return
            }
            outfile, err := os.Create(target_path)
            if err != nil {
                log.Error(err)
                return
            }
            err = tmpl.Execute(outfile, context)
            outfile.Close()
            if err != nil {
                log.Error(err)
                return
            }
        }
    }
    // go through all files in the template directory and apply the template to the output dir
    filepath.Walk(template_name, func(path string, info os.FileInfo, err error) error {
        if err != nil {
            return err
        }
        relpath, err := filepath.Rel(template_name, path)
        if err != nil {
            return err
        }
        if relpath == "." || relpath == ".." {
            return nil
        }
        log.Info("Processing", relpath)
        target_path := filepath.Join(target_dir, relpath)
        if info.IsDir() {
            os.Mkdir(target_path, 0755)
        } else {
            // process template
            tmpl, err := template.New(info.Name()).ParseFiles(path)
            if err != nil {
                return err
            }
            outfile, err := os.Create(target_path)
            if err != nil {
                return err
            }
            err = tmpl.Execute(outfile, context)
            outfile.Close()
            if err != nil {
                return err
            }
        }
        return nil
    })
}

var Jobs_commands = []cli.Command{
    {
        Name: "init",
        Aliases: []string{"i"},
        Usage: "Initialize a new job type in the current or specified directory. Does not modify scale.",
        ArgsUsage: "[destination path]",
        Flags: []cli.Flag{
            cli.StringFlag{
                Name: "template-path",
                Usage: "Template search path",
                EnvVar: "SCALE_TEMPLATE_PATH",
            },
            cli.BoolFlag{
                Name: "force, f",
                Usage: "Force overrite of existing destiation path",
            },
            cli.StringFlag{
                Name: "template",
                Usage: "Specifies a template for the new job type. If not specified, a default will be used.",
            },
            cli.StringSliceFlag{
                Name: "arg, a",
                Usage: "Specify an argument for the template in the key=val format",
            },
        },
        Action: jobs_template,
    },
}
