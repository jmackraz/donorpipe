# Manual Data Updates
We have some manual data updates that we need to handle, including our QBO report, which 
the user will want to see updated quickly in the app.

## General Operations
* We collect CSV files in an offline data warehouse
* From the files that warehouse, we create a data graph json file
* From the warehouse, we use warehouse/sync-data.sh to push the graph out to the staging or production servers.

## Updates
* We can update the csv files from Stripe and DonorBox automatically on a schedule, and then update the graph and sync.
* However, we cannot automatically download Benevity reports, so they will be manually updated.
* We may not be able to download our QBO report CSV with automation
* Important: In the normal workflow, the bookkeeper will use our app to make additions and corrections to sales receipts
in QBO. They will want to see their changes in the app in short order.

## Workflow 1
* User manually downloads some CSV reports to a shared location accessible to the warehouse
* The warehouse learns by polling or something more modern that files have been updated
* The warehouse updates the graph and syncs the data.


## Google Drive
The best solution for users would be to use Google Drive, as part of Google for Workplace (Non-Profits)

In order of preference, the warehouse could run on:
1. A raspberry pi without a desktop manager
2. A raspberry pi with Gnome Desktop Manager
3. A Mac with Google Drive Finder extension

Case 1 might require use of the Google API, or new Goole Office CLI, and an involved setup process on Google.
Case 2 might require unwelcome setup and resource use for Gnome.
Case 3 probably works fine, but might not behave exactly like a local file system.

## Questions
### Some options for detecting new data
1. Record and compare the latest last-modified date of all the files in the warehouse.  Probably easiest if the
last-modified date is reliable on Google Drive.
2. Record a manifest of all the files used to generate the graph, with checksums of their contents.

It probably makes sense to record these data directly in the generated graph. Then the semantics become simply: "Are
there any files newer than the graph?"

