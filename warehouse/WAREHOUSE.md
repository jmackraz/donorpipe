# Warehouse and processing for CSV reports

This project centralizes the collection, processing and deployment of CSV reports
from various services. 

## Notes
* This is sub-project of donorpipe. It will not be a git submodule.
* This code in this project runs only on the development server or in-house management server.
* We expect that this subproject's function may be useful for other projects,
and we will want to factor it out into a separate project in the future. I won't care about taking
the git history with it.
* Some things we've got in donorpipe might be moved here, including:
  * rsync examples in doc files
  * the sanitization scripts
* IMPORTANT: you should not look at the real, unsanitized data in this project.

## Phase 1 - Sanitization and deployment

### Goals
* Manage the local collection and repository of CSV reports from various services.
* Includes scripts to sanitize the reports, without knowing details of the schema.
* Centralizes configuration and operations of how the reports are deployed to staging and production.

### Configuration and intent
* We will have multiple directories of real data, for different organizations.  For now, there is only 'oliveseed'.
* We will create a directory of sanitized data, from one of the sets of real data, and use that for local dev testing,
and an account (test_org) we use for demos staging and production.
* This means that deployment knows nothing about whether it's pushing real or sanitized data.
* Santization will need an independent block in the config file. It should be able
to specify more than one sanitization operation, which for now includes a source directory (of real
data) and a destination of sanitized data.  Someday we may include operation-specific options.
* The deployment configuration file specifies the source directory for each account.  As mentioned,
the directory for 'oliveseed' will be the real data. The directory for 'test_org' will be the sanitized data.  
This is true for both staging and production.

### Behaviors
* A script creates or refreshes the sanitized data from the real data
* A script of our paradigm (PROD=1 scripts/<command>) deploys data to staging and production
* The deployments are also specified in the configuration file to reduce dependencies on command-line arguments

### Done when
* We can create a sanitized repository from the complete set of our real data.

## Phase 2 - Download automation

### Goals
* Create a suite of scripts to automate the download of reports from various services.
* Set up operations automated refresh of all data

### Notes
* Each script will be using a service-specific API, and may include some specific libraries
or other files. Each service gets its own subdirectory.

### Behaviors
* A family of scripts can download reports from all services offering an API
* An automated or semi-manual process is implemented to collect reports for services with no API.
* The download, collection and sanitization processes are automated to repeat

