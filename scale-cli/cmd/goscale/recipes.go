package main

import (
    "github.com/ngageoint/scale/scale-cli"
    "github.com/codegangsta/cli"
    "github.com/fatih/color"
    "strconv"
    "fmt"
)

func recipes_run(c *cli.Context) {
    url := c.GlobalString("url")
    if url == "" {
        log.Fatal("A URL must be provided with the SCALE_URL environment variable or the --url argument")
        return
    }
    if c.NArg() != 1 && c.NArg() != 2 {
        log.Fatal("Must specify a single recipe type name or id.")
        return
    }
    var recipe_type scalecli.RecipeType
    found := false
    id, err := strconv.Atoi(c.Args()[0])
    if err == nil {
        var resp_code int
        recipe_type, resp_code, err = scalecli.GetRecipeTypeDetails(url, id)
        if err != nil && resp_code != 404 {
            log.Fatal(err)
            return
        } else if err == nil {
            found = true
        }
    }
    if !found {
        name := c.Args()[0]
        recipe_types, err := scalecli.GetRecipeTypes(url)
        if err != nil {
            log.Fatal(err)
            return
        }
        var version string
        if c.NArg() == 2 {
            version = c.Args()[1]
        }
        switch(len(recipe_types)) {
        case 0:
            log.Fatal("Recipe type not found.")
            return
        case 1:
            recipe_type = recipe_types[0]
            found = true
            break
        default:
            for _, rt := range recipe_types {
                if rt.Name == name && rt.Version == version {
                    recipe_type = rt
                    found = true
                    break
                }
            }
            if !found {
                log.Error("Multiple recipe types found")
                for _, rt := range recipe_types {
                    fmt.Printf("%4d %8s [%25s] - %s\n", rt.Id, rt.Version, rt.Name, rt.Title)
                }
                return
            }
        }
    }
    data_file := c.String("data")
    var recipe_data scalecli.RecipeData
    err = Parse_json_or_yaml(data_file, &recipe_data)
    if err != nil {
        log.Fatal(err)
        return
    }
    update_location, err := scalecli.RunRecipe(url, recipe_type.Id, recipe_data)
    if err != nil {
        log.Fatal(err)
        return
    }
    color.Blue(fmt.Sprintf("Recipe submited, updates available at %s", update_location))
}

var Recipes_commands = []cli.Command{
    {
        Name: "run",
        Usage: "Run a new recipe.",
        ArgsUsage: "<Recipe type ID> | [<recipe type name> <recipe type version>]",
        Flags: []cli.Flag{
            cli.StringFlag{
                Name: "data, d",
                Usage: "Recipe data file (json or yaml).",
            },
        },
        Action: recipes_run,
    },
}
