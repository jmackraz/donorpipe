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

# API/Download Notes

## Stripe
Stripe has test api keys.  Not sure if they return fake data.
We download transactions, not reports. Our headers are:
id,Type,Source,Amount,Fee,Destination Platform Fee,Destination Platform Fee Currency,Net,Currency,Created (UTC)
Available On (UTC),Description,Customer Facing Amount,Customer Facing Currency,Transfer,Transfer Date (UTC)
Transfer Group,description (metadata),

donorbox_address_line_2 (metadata),donorbox_country (metadata),donorbox_idempotency_key (metadata)
donorbox_gift_aid (metadata),donorbox_plan_interval (metadata),donorbox_donation_type (metadata)
donorbox_form_id (metadata),donorbox_postal_code (metadata),donorbox_state (metadata),donorbox_city (metadata)
donorbox_address (metadata),donorbox_donor_id (metadata),donorbox_recurring_donation (metadata)
donorbox_name (metadata),donorbox_last_name (metadata),donorbox_first_recurring_charge (metadata)
donorbox_first_name (metadata),donorbox_email (metadata),donorbox_designation (metadata),donorbox_campaign (metadata)

GPT says the closest API is "Balance Transactions"  It's return schema:
The Balance Transaction object (example)
{
  "id": "txn_1MiN3gLkdIwHu7ixxapQrznl",
  "object": "balance_transaction",
  "amount": -400,
  "available_on": 1678043844,
  "created": 1678043844,
  "currency": "usd",
  "description": null,
  "exchange_rate": null,
  "fee": 0,
  "fee_details": [],
  "net": -400,
  "reporting_category": "transfer",
  "source": "tr_1MiN3gLkdIwHu7ixNCZvFdgA",
  "status": "available",
  "type": "transfer"
}
