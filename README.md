Do not merge

# development

This repository is used for developing and testing worklows and scripts for the charts and stage repositories.

# Release process

Periodically the workflows and scripts from this repository will be "released" into the charts for live use by chart submitters and stage repository to be used for chart submission testing. At the same time any charts added to the charts repository will be added to this repository. This is an automated process which can be started by any approver of the repository.

To start the proecess:
1. Modify the [release/release_info.json](https://github.com/openshift-helm-charts/development/blob/main/release/release_info.json) file with information about the release. Information includes:
   - The version of the new release.
   - Information to describe the content of the release.
   - For each of the chart, development and stage repository.
     - merges: a directory/file which is to be merged with the same directory in the other repository. 
     - replaces : a directory/file which will be deleted from the other repository and replaced with the same directory/file from the specifying repository. This also covers new directories added.
     - ignores : a directory or files which is part of the merge or replace but should be excluded. This also covers deleted files.
   - For example, release/release_info.json for the charts repository specifies a merge of the charts directory. This means the charts of the charts repository will be merged into the same directory in the development repository. This effectively updates the development repository with the charts which were added since that last release.
   - For example, release/release_info.json for the development repository specifies a replace of the scripts directory. This means the scripts directory will be deleted from the charts repository and replaced with the scripts directory and its contents from the development repository.
   - For example, release/release_info.json for the development repository specifies an ignore of the .github/workflows/release.yml file. This means after copying the entire content of the .github directory to the charts repository the specific file will then be removed. 
1. Create a Pull Request against the development repository containing only the release/release_info.json. The release workflow then:
    1. Clones the development, charts and stage repositories.
    1. Updates each of the repositories based on the content of the release/release_info.json.
    1. Creates a pull request against the chart repository containing workflow updates from the development repository.
        - This PR will need to be manually merged once all tests are finished and clean.
    1. Creates a pull request against the stage repository containing workflow updates from the development repository.
        - This PR will also need to be manually merged once all tests are finished and clean.
    1. Creates a pull request against the development repository containing chart updates from the chart repository.
        - This PR will be auto-merged in subsequent steps.
    1. Assuming all is good, auto-merges the release/release_info.json pull request.
        - Also creates a release if the development repository pull request is not required.
    1. Detects the incoming pull request against the development repository, merges it and creates a release. 

