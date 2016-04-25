package main

import (
    "github.com/ngageoint/scale/scale-cli"
    "github.com/codegangsta/cli"
    "os"
    "errors"
    "strconv"
    "syscall"
    "path/filepath"
    "text/template"
    "strings"
    "github.com/docker/docker/builder/dockerfile/parser"
    "bufio"
    "io"
    "encoding/json"
    "os/exec"
)

// hardcoded defaults
var defaults = map[string]string{
    "Dockerfile": `FROM {{ .baseimage }}
MAINTAINER {{ .maintainer }}

# The job type definition. Don't edit this, use job_type.json or job_type.yml as this will be replaced
LABEL com.ngageoint.scale.job-type=""
###

RUN useradd --uid 1001 scale
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

    ".dockerignore": `job_type.json
job_type.yml
`,
}

func get_label_value(dockerfile_name string, label_name string) (label_value string, err error) {
    f, err := os.Open(dockerfile_name)
    if err != nil {
        return
    }
    defer f.Close()
    ast, err := parser.Parse(f)
    if err != nil {
        return
    }
    // root node only has children and represents the entire file
    for _, n := range ast.Children {
        if n.Value == "label" {
            // found a label statement, see if it has our label
            for nn := n.Next; nn != nil; nn = nn.Next.Next {
                if nn.Value == label_name {
                    nn = nn.Next
                    label_value, err = strconv.Unquote(nn.Value)
                    return
                }
            }
        }
    }
    return "", nil
}

func get_docker_image_name() (docker_image string, err error) {
    json_data, err := get_label_value("Dockerfile", "com.ngageoint.scale.job-type")
    if err != nil {
        log.Error(err)
        return
    } else if json_data == "" {
        log.Error("Unable to find image name")
        return
    }

    var job_type scalecli.JobType
    err = json.Unmarshal([]byte(json_data), &job_type)
    if err != nil {
        log.Error(err)
        return
    }
    docker_image = job_type.DockerImage
    return
}

func set_label_value(dockerfile_name string, label_name string, label_value string) error {
    f, err := os.Open(dockerfile_name)
    if err != nil {
        return err
    }
    defer f.Close()
    ast, err := parser.Parse(f)
    if err != nil {
        return err
    }
    // root node only has children and represents the entire file
    for _, n := range ast.Children {
        if n.Value == "label" { // found a label statement, see if it has our label
            newval := "LABEL " // build the new output as we go
            first := true
            found := false
            for nn := n.Next; nn != nil; nn = nn.Next {
                if first {
                    first = false
                } else {
                    newval += " \\\n "
                }
                newval += nn.Value + "="
                if nn.Value == label_name {
                    found = true
                    nn = nn.Next
                    newval += strconv.Quote(label_value)
                } else {
                    nn = nn.Next
                    newval += nn.Value
                }
            }
            if found {
                // replace the value in the file and end
                outf, err := os.Create(dockerfile_name + ".tmp")
                if err != nil {
                    return err
                }
                defer outf.Close()
                f.Seek(0, os.SEEK_SET)
                rdr := bufio.NewReader(f)
                for line := 1; ; line++ {
                    if line == n.StartLine {
                        outf.WriteString(newval + "\n")
                    } else {
                        buf, isPrefix, err := rdr.ReadLine()
                        if err == io.EOF {
                            break
                        } else if err != nil {
                            return err
                        } else if isPrefix {
                            return errors.New("Line "+string(line+1)+" is too long")
                        }
                        if line < n.StartLine || line > 1+n.EndLine {
                            outf.Write(buf)
                            outf.WriteString("\n")
                        }
                    }
                }
                os.Remove(dockerfile_name)
                os.Rename(dockerfile_name + ".tmp", dockerfile_name)
                break
            }
        }
    }
    return nil
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

func jobs_commit(c *cli.Context) {
    // push json into Dockerfile
    var job_type scalecli.JobType
    err := Parse_json_or_yaml("job_type", &job_type)
    if err != nil {
        log.Error(err)
    }
    json_data, err := json.Marshal(job_type)
    if err != nil {
        log.Error(err)
    }
    err = set_label_value("Dockerfile", "com.ngageoint.scale.job-type", string(json_data))
    if err != nil {
        log.Error(err)
    }

    // build the docker image
    docker_image, err := get_docker_image_name()
    if err != nil {
        log.Error(err)
        return
    }
    log.Info("Building", docker_image)
    cmd := exec.Command("docker", "build", "-t", docker_image, ".")
    output, err := cmd.CombinedOutput()
    if err != nil {
        log.Error(err, string(output))
        return
    }
    log.Info(string(output))

    if c.Bool("push") {
        jobs_push(c)
    }
}

func jobs_push(c *cli.Context) {
    // push the image
    docker_image, err := get_docker_image_name()
    if err != nil {
        log.Error(err)
        return
    }
    log.Info("Pushing", docker_image)
    cmd := exec.Command("docker", "push", docker_image)
    output, err := cmd.CombinedOutput()
    if err != nil {
        log.Error(err, string(output))
        return
    }
    log.Info(string(output))
}

func jobs_deploy(c *cli.Context) {
    // pull the image
    err := error(nil) // some weird scoping issues if we don't declare here
    docker_image := c.String("image")
    if docker_image == "" {
        docker_image, err = get_docker_image_name()
        if err != nil {
            log.Error(err)
            return
        }
    }
    if c.Bool("pull") {
        log.Info("Pulling", docker_image)
        cmd := exec.Command("docker", "pull", docker_image)
        _, err = cmd.CombinedOutput()
        if err != nil {
            log.Warning("Unable to pull the image. Checking if it is locally available.")
        }
    }

    // extract the JSON
    cmd := exec.Command("docker", "inspect", "-f", "{{(index .Config.Labels \"com.ngageoint.scale.job-type\")}}", docker_image)
    output, err := cmd.CombinedOutput()
    if err != nil {
        log.Error(err, string(output))
        return
    }
    var job_type scalecli.JobType
    err = json.Unmarshal([]byte(output), &job_type)
    if err != nil {
        log.Error(err)
        return
    }

    log.Info(job_type) // debug outout

    // check for existing job type
    // fill in missing data (new version if necessary)
    // submit the job type
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
    {
        Name: "commit",
        Aliases: []string{"build"},
        Usage: "Updates the job type config, and build the docker image for the current directory.",
        Flags: []cli.Flag{
            cli.BoolFlag{
                Name: "push, p",
                Usage: "Also perform a push to the docker index after building.",
            },
        },
        Action: jobs_commit,
    },
    {
        Name: "push",
        Usage: "Push the docker image to the docker index.",
        Action: jobs_push,
    },
    {
        Name: "deploy",
        Usage: "Deploy an algorithm to scale, either from the current directory or specify an image name.",
        Flags: []cli.Flag{
            cli.StringFlag{
                Name: "image, i",
                Usage: "Specify the image to deploy. If not specify, obtain this from the current directory.",
            },
            cli.BoolFlag{
                Name: "pull, p",
                Usage: "Should the image be pulled first?",
            },
        },
        Action: jobs_deploy,
    },
}
