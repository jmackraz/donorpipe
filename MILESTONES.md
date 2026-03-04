# Milestone Plan for DonorPipe

## Overview
All steps should be implemented in line with the memorized plan.

The first milestone will help us set up some durable test data files.  All further milestones can
use these files for their automated tests.

## Milestones
### Milestone 1: Set up project directory hierarchy

**Goal:** Directory src tree set up for best practices, to include:
* Backend models (python) and data layer
* API bindings, routes, config (for FastAPI)
* Front-end React/TypeSCript project
* CLI script
* Development scripts

### Milestone 2: Sanitized test data

**Goal:** provide a utility to sanitize CSV financial reports for use as durable test data
It is assumed that future milestones will need meaningfully rich and realistic data set, 
but production data contains sensitive information.

**Form:** a command-line python utility script that will be run outside the context of the project

**Behavior:** 
* parameters: input directory and output directory
* all CSV files in the input directory and descendants are processed to create output 
files under the output directory, in the same subdirectory structure
* processing consists of replacing the values in any column with header value containing:
'name', 'address', 'comment'
* the replacement values do not need to be believable or appealing for a demo.  For example, 
the names could be "Name 123", "Name 124" etc.  I'm open to a better way if it's not too complex.
* the value encoding format should not be changed.  It may be best to interpret fields as strings.

**Constraints:**
* Standard libraries only, but ask if worth it

**Complete when:**
* Test uses synthesized data files
* script is available in a development scripts directory
* Test suite succeeds

### Milestone 3.1: Adapt legacy backend

Before implementing this, we should discuss submilestones.

**Precondition:**
* I have copied legacy code into the 'models' directory
and two files that make up the CLI script into the 'cli' directory.
* In so doing, I relocated the two cli files, which were originally
in the same directory as the models.

**Goals:**
* The legacy code runs successfully in this project structure

The cli command, from the top level project directory is:

```bash
env OSF_EXPORTS=testdata uv run src/donorpipe/cli/model_cli.py -d Stripe DonorBox QBO
```

**Behavior:**
* The legacy code has been analyzed and remembered
* The CLI script executes without exception and ingests the test data

**Done when:**
* The CLI functions
* User confirms the CSVs are being ingested

### Milestone 3.2: Improve the legacy code

**Goals:the legacy code is improved**

**Behavior:**
* The legacy code is typed
* The legacy code has automated tests
* Suggestions are discussed and implemented, with decisions recorded

**Done when:**
* The legacy code is typed
* Test suite succeeds
* Suggestions are implemented
* Decisions are documented

**Constraints:**
* Don't refactor the legacy code

**Decisions:**
* Type checker: pyright
* Testing: light unit tests; code is stable and well-exercised
* Pydantic: deferred to Milestone 5 where FastAPI integration makes it natural
* Type annotations: inline PEP 484 hints, no structural refactoring


### Milestone 4: Serialize graph

**Goal:** Prepare payloads for fetching the transaction graph


### Milestone 5: API

**Goal:** Bring up a REST API exposing the backend

**Behavior:**
* One GET method returns the serialized graph
  * It takes a single parameter as a stub for the 'oganization account id'
* A simple CLI script (python) demonstrates how to fetch and decode the graph
* The backend will need a configuration file scheme to replace the parameters
provided today by the CLI

### Milestone 6: CLI uses the API

**Goal:** Make a modified version of the legacy CLI that uses the API instead of direct
import of the backend.

### Milestone 7: Core TypeScript functionality

**Goal:** Get the deserialization and object model working for JavaScript in a CLI context

**Behavior:**
* New javascript CLI script runs under Node or similar (please recommend)
* script connects to API, retreives serialized graph
* deserialized the transaction object graph
* has a suitable amount of transaction class abstractions and helper methods,
as modeled on the legacy code
* Organized suitably modular so that the core code can be imported into the web app.

**Done when:**
* Tests written to validate 

### Milestone 8: Skeletal Front-End

**Goal:** Bring up a React/TypeScript subproject that connects to the backend as a minimal
responsive app

**Non-goals:**
* Complex styling
* Fancy controls/UI
* Auth

**Behavior:**
* App runs in Chrome
* App incorporates code from prior milestone
    * Connects to API and fetches serialized graph
    * Deserializes into object graph
* Displays some selection of data in a simple scrolling viej

**Guidelines:**
* Prefer simplicity over performance optimization

**Done when:**
Let's discuss.  I do not know the best practices for testing web apps.  It may
be more complex than necessary.

The test and acceptace criteria may be human.

* The app is tested in Chrome
* A single GET, decode, display is tested from the app
* The backend does not throw exceptions
* The page loads succesfully
* The Chrome logs are clean of errors and warnings

### Milestone 9: UX Function

**Goal:** The primary views and responsive layout of the app are in place

**Non-goal:** Fancy styling, theming, tranisitions

We should discuss our approach to specifying the UX features and layout I have in mind.

### Milestone 10: Nice styling and polish

**Goal:** Upgrade the UX design to high standards

### Milestone 11: Auth and Account silos

**Goal:** Implement credentials management and security at the data partition level

### Milestone 12: Local Deployment

**Goal:** Host the app on my RaspPi for use locally

**Behavior:**
* Modern, simple approach to packaging front and back end
* Deployment for stable environments
* Simple hotfix capability

### Milestone 13: Public Deployment

**Goal:** Make app available to a small audience by cloud hosting

**Requirements:**
* Password auth
* HTTPS protocol
* Reproducible instantiation, e.g. CloudFormation

**Discussion:**
AWS is my general choice. For simplicity, I'd like to deploy with FastAPI at first,
rather than involving AWS API Gateway.  I have a lightsail instance we could use,
but I don't know about HTTPS with it.  I'd be inclined to do something that can 
be fully specified in CloudFormation or someothing.  But if the minimal instance configuration 
is much more expensive than a Lightsail solution, I'd lean toward Lightsail now and
migrate to serverless API Gateway with lambdas later.

