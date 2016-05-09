package main

import (
    "github.com/ngageoint/scale/scale-cli"
    "github.com/codegangsta/cli"
    "github.com/fatih/color"
    "github.com/docker/docker/builder/dockerfile/parser"
    "os"
    "errors"
    "strconv"
    "syscall"
    "path/filepath"
    "text/template"
    "strings"
    "bufio"
    "io"
    "encoding/json"
    "os/exec"
    "fmt"
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
    "job_type.yml": `---
name: {{ .name }}
version: "1.0.0"
title: {{ .name }}
description: {{ .description }}
author_name: "{{ .maintainer }}"
docker_image: "{{ .image_name }}"
priority: 250
timeout: 300
max_tries: 3
cpus_required: 1.0
mem_required: 512.0
interface:
  version: "1.0"
  command: "./entryPoint.sh"
  command_arguments: "${input_file} ${job_output_dir}"
  output_data:
    - type: file
      required: true
      name: output_file
  input_data:
    - required: true
      type: file
      name: input_file
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
                    label_value, err = strconv.Unquote(strings.Replace(nn.Value, "$ {", "${", -1))
                    return
                }
            }
        }
    }
    return "", nil
}

func get_docker_image_name(c *cli.Context) (docker_image string, err error) {
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
    docker_registry := c.GlobalString("registry")
    if docker_registry == "" || strings.HasPrefix(job_type.DockerImage, docker_registry) {
        docker_image = job_type.DockerImage
    } else {
        docker_image = docker_registry + "/" + job_type.DockerImage
    }

    docker_tag := c.GlobalString("tag")
    if docker_tag == "" || strings.HasSuffix(job_type.DockerImage, docker_tag) {
        docker_image = job_type.DockerImage
    } else {
        docker_image = job_type.DockerImage + ":" + docker_tag
    }
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
                    newval += strings.Replace(strconv.Quote(label_value), "${", "$ {", -1)
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

func jobs_template(c *cli.Context) error {
    // locate the template...if none is specified, fall back to a hard coded default
    template_name := c.String("template")
    if template_name != "" {
        template_path := c.GlobalString("template-path")
        tmp, err := find_template_in_path(template_name, template_path)
        if err != nil {
            return cli.NewExitError(err.Error(), 1)
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
            return cli.NewExitError("Target exists and is not a directory.", 1)
        } else if c.Bool("f") {
            log.Warning("Target directory",strconv.Quote(target_dir),"exists. Overriting contents.")
        } else {
            return cli.NewExitError(fmt.Sprint("Target directory", strconv.Quote(target_dir), "exists. Use -f to overrite."), -1)
        }
    } else {
        if e, ok := err.(*os.PathError); ok && e.Err == syscall.ENOENT {
            os.MkdirAll(target_dir, 0755)
        } else {
            return cli.NewExitError(err.Error(), 1)
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
                return cli.NewExitError(err.Error(), 1)
            }
            outfile, err := os.Create(target_path)
            if err != nil {
                return cli.NewExitError(err.Error(), 1)
            }
            err = tmpl.Execute(outfile, context)
            outfile.Close()
            if err != nil {
                return cli.NewExitError(err.Error(), 1)
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
    return nil
}

func jobs_commit(c *cli.Context) error {
    // push json into Dockerfile
    var job_type scalecli.JobType
    err := Parse_json_or_yaml("job_type", &job_type)
    if err != nil {
        return cli.NewExitError(err.Error(), 1)
    }
    registry := c.GlobalString("registry")
    if registry != "" {
        if !strings.HasPrefix(job_type.DockerImage, registry) {
            job_type.DockerImage = registry + "/" + job_type.DockerImage
        }
    }
    tag := c.GlobalString("tag")
    if tag != "" {
        if !strings.HasSuffix(job_type.DockerImage, tag) {
            job_type.DockerImage = job_type.DockerImage + ":" + tag
        }
    }
    json_data, err := json.Marshal(job_type)
    if err != nil {
        return cli.NewExitError(err.Error(), 1)
    }
    err = set_label_value("Dockerfile", "com.ngageoint.scale.job-type", string(json_data))
    if err != nil {
        return cli.NewExitError(err.Error(), 1)
    }

    // build the docker image
    docker_image, err := get_docker_image_name(c)
    if err != nil {
        return cli.NewExitError(err.Error(), 1)
    }
    log.Info("Building", docker_image)
    cmd := exec.Command("docker", "build", "-t", docker_image, ".")
    output, err := cmd.CombinedOutput()
    if err != nil {
        return cli.NewExitError(string(output), 1)
    }
    log.Info(string(output))

    if c.Bool("push") {
        jobs_push(c)
    }
    return nil
}

func jobs_push(c *cli.Context) error {
    // push the image
    docker_image, err := get_docker_image_name(c)
    if err != nil {
        return cli.NewExitError(err.Error(), 1)
    }
    log.Info("Pushing", docker_image)
    cmd := exec.Command("docker", "push", docker_image)
    output, err := cmd.CombinedOutput()
    if err != nil {
        return cli.NewExitError(err.Error(), 1)
    }
    log.Info(string(output))
    return nil
}

func jobs_validate(c *cli.Context) error {
    var job_type scalecli.JobType
    err := Parse_json_or_yaml("job_type", &job_type)
    if err != nil {
        return cli.NewExitError(err.Error(), 1)
    }

    url := c.GlobalString("url")
    if url == "" {
        return cli.NewExitError("A URL must be provided with the SCALE_URL environment variable or the --url argument", 1)
    }
    warnings, err := scalecli.ValidateJobType(url, job_type)
    if err != nil {
        return cli.NewExitError(err.Error(), 1)
    }
    if warnings == "" {
        color.White("Job type specification is valid.")
    } else {
        color.Yellow(warnings)
    }
    return nil
}

func jobs_deploy(c *cli.Context) error {
    // pull the image
    err := error(nil) // some weird scoping issues if we don't declare here
    docker_image := c.String("image")
    if docker_image == "" {
        docker_image, err = get_docker_image_name(c)
        if err != nil {
            return cli.NewExitError(err.Error(), 1)
        }
    } else  {
        if c.GlobalString("registry") != "" {
            docker_image = c.GlobalString("registry") + "/" + docker_image
        }
        if c.GlobalString("tag") != "" {
            docker_image = docker_image + ":" + c.GlobalString("tag")
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
        return cli.NewExitError(err.Error(), 1)
    }
    json_value := strings.Replace(string(output), "$ {", "${", -1)
    if strings.TrimSpace(json_value) == "" {
        return cli.NewExitError(fmt.Sprint("Scale job type information not found in", docker_image), 1)
    }
    var job_type scalecli.JobType
    err = json.Unmarshal([]byte(json_value), &job_type)
    if err != nil {
        return cli.NewExitError(err.Error(), 1)
    }

    url := c.GlobalString("url")
    if url == "" {
        return cli.NewExitError("A URL must be provided with the SCALE_URL environment variable or the --url argument", 1)
    }

    if c.Bool("n") {
        // validate only
        warnings, err := scalecli.ValidateJobType(url, job_type)
        if err != nil {
            return cli.NewExitError(err.Error(), 1)
        }
        if warnings == "" {
            color.White("Job type specification is valid.")
        } else {
            color.Yellow(warnings)
        }
        return nil
    }

    // check for existing job type
    job_types, err := scalecli.GetJobTypes(url, job_type.Name)
    if err != nil {
        return cli.NewExitError(err.Error(), 1)
    }
    if len(job_types) == 0 {
        // create a new job type
        log.Info("Creating new job type entry")
        err = scalecli.CreateJobType(url, job_type)
        if err != nil {
            return cli.NewExitError(err.Error(), 1)
        }
    } else {
        for _, jt := range job_types {
            if jt.Version == job_type.Version {
                // found an exising entry, either update or create a new one
                log.Info("Updating job type metadata", jt.Id)
                err = scalecli.UpdateJobType(url, jt.Id, job_type)
                if err != nil {
                    return cli.NewExitError(err.Error(), 1)
                }
                return nil
            }
        }
        // no entry found, create a new one
        log.Info("Creating new job type entry for", job_type.Name, "version", job_type.Version)
        err = scalecli.CreateJobType(url, job_type)
        if err != nil {
            return cli.NewExitError(err.Error(), 1)
        }
    }
    return nil
}

func jobs_run(c *cli.Context) error {
    url := c.GlobalString("url")
    if url == "" {
        return cli.NewExitError("A URL must be provided with the SCALE_URL environment variable or the --url argument", 1)
    }
    if c.NArg() != 1 && c.NArg() != 2 {
        return cli.NewExitError("Must specify a single job type name or id.", 1)
    }
    var job_type scalecli.JobType
    found := false
    id, err := strconv.Atoi(c.Args()[0])
    if err == nil {
        var resp_code int
        job_type, resp_code, err = scalecli.GetJobTypeDetails(url, id)
        if err != nil && resp_code != 404 {
            return cli.NewExitError(err.Error(), 1)
        } else if err == nil {
            found = true
        }
    }
    if !found {
        job_types, err := scalecli.GetJobTypes(url, c.Args()[0])
        if err != nil {
            return cli.NewExitError(err.Error(), 1)
        }
        var version string
        if c.NArg() == 2 {
            version = c.Args()[1]
        }
        switch(len(job_types)) {
        case 0:
            return cli.NewExitError(err.Error(), 1)
        case 1:
            job_type = job_types[0]
            found = true
            break
        default:
            for _, jt := range job_types {
                if jt.Version == version {
                    job_type = jt
                    found = true
                    break
                }
            }
            if !found {
                for _, jt := range job_types {
                    fmt.Printf("%4d %8s [%25s] - %s\n", jt.Id, jt.Version, jt.Name, jt.Title)
                }
                return cli.NewExitError("Multiple job types found", 1)
            }
        }
    }
    data_file := c.String("data")
    var job_data scalecli.JobData
    err = Parse_json_or_yaml(data_file, &job_data)
    if err != nil {
        return cli.NewExitError(err.Error(), 1)
    }
    update_location, err := scalecli.RunJob(url, job_type.Id, job_data)
    if err != nil {
        return cli.NewExitError(err.Error(), 1)
    }
    color.Blue(fmt.Sprintf("Job submited, updates available at %s", update_location))
    return nil
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
        Name: "validate",
        Usage: "Validate the job_type data in job_type.json or job_type.yml.",
        Action: jobs_validate,
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
            cli.BoolFlag{
                Name: "n",
                Usage: "Pull the image and validate only, don't submit to Scale.",
            },
        },
        Action: jobs_deploy,
    },
    {
        Name: "run",
        Usage: "Run a new job.",
        ArgsUsage: "[Job type ID | job type name]",
        Flags: []cli.Flag{
            cli.StringFlag{
                Name: "data, d",
                Usage: "Job data file (json or yaml).",
            },
        },
        Action: jobs_run,
    },
}
